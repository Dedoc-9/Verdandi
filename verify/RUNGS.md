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
in the oracle as evidence and is not minted here; since ORACLE-D0 (below) it is recomputed at gate time by Urðr's
own `statecanon`, in place, and still never by the kernel. Any frame budget (off-gate:
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

**RE-BREAKDOWN-1b (the constant-anchor refinement, before any layout change).** The first host run's Court B increments
were close (tile-fetch 1071 vs map/assembly 911 µs p99) and the negative control was large (`full − emit` ≈ 1079 µs) —
because the 1a probe accumulated 1/2/3 anchor values by mode, so its `black_box` tax grew with depth and leaked into the
deltas. Choosing rigor over speed, 1b rebuilds the probe (`anchor_of`) so **every mode folds exactly three bytes with the
identical combine** — ADDR from the address, LOOKUP from the tile texels, FULL/VERIFY from the band-map results — leaving
only the memory work under measurement to differ. The tax is now constant across modes and cancels: `LOOKUP − ADDR` is
the tile fetch alone, `FULL − LOOKUP` the map indirection alone. `emit_probe<VERIFY>` stays byte-identical to emit, the
fence and the deterministic Court A are unchanged (the gate is byte-identical, rowset `2fd691b4a383354c`), so this is a
same-court instrument refinement, not a new method. It re-seats under the same hash-locked RE-BREAKDOWN-1 entry; the host
re-measures (`verify/rebreakdown1.py`, now default 500/50) and the promotion call is made from the de-contaminated
increments. In the container the refinement widened the tile-fetch lead from ~1.2× to ~4× and shrank the negative control
by roughly half — the host number is the user's, and the LOCALITY court is chosen from it.

## LOCALITY-0 — the floor-tile execution-format court (blocked vs Morton, process-isolated) (seat 18)

**What landed (a two-layout court under a new isolation law).** RE-BREAKDOWN-1b named the tile fetch as emit's leading
cost (a clean ~4.4× over the map indirection once the anchor tax was cancelled). LOCALITY-0 attacks it by re-laying-out
the **floor tile's storage** — the execution FORMAT — while the frozen `mantle.rs` and the accepted DDA `fast::emit`
stay untouched. Two layouts compete, each a lossless bijection proven byte-identical to the frozen oracle: **BLOCKED**
(8×8 cache blocks, cheap shift/mask index) and **MORTON** (Z-order space-filling curve, portable scalar bit-interleave,
a heavier index). `kernel/fast.rs::locality` holds `swizzle_index<LAYOUT>`, the `swizzle_tile`/`unswizzle_tile`
permutation, and `emit_swizzled<LAYOUT>` — the DDA emit with the floor fetched from the re-laid-out copy. LINEAR is the
identity and reproduces `fast::emit` byte-for-byte (the apparatus anchor).

**The isolation law it introduced.** The court is built on the author's *Epistemic Invariance of the Boundary*
theorem (`EPISTEMIC-INVARIANCE.md`): two layouts are neither timed in one process (which poisons the branch predictor
and bloats the I-cache until a data-locality test becomes an instruction-locality test) nor in two loose runs (which
leaks thermal drift). Instead the *same* binary is hot-swapped by `--variant`, one layout per process, and the
invocations are **interleaved in alternating strips** so slow drift cancels; each variant is timed against a DDA
baseline measured in *its own* process, and the orchestrator compares the two baseline-relative improvements (medians
across strips). Monomorphize, process-isolate, interleave — and prove *output* invariance, not instruction invariance.

**Objectives, each to a mechanism.** (1) *Proof of the memory bottleneck* — the only thing that changes is the tile
layout, so byte-identical-and-faster is causal proof the fetch was the cost. (2) *Absolute regression security* —
`locality0-equiv` (both layouts byte-identical over corpus + adversarial cameras) **and** a non-vacuous synthetic
distinct-per-texel render, because the corpus floor is flat and would make the naive test vacuous. (3) *Clean
progression signal* — `--locality-bench` vs the DDA baseline, process-isolated. (4) *Oracle purity* — the swizzle is a
fast-path scene-load transform; `mantle.rs`/`fast::emit` untouched, the witnesses unchanged. (5) *Index-arithmetic
verdict* — the floor ADDR ablation isolates each layout's tax X (blocked cheap, Morton heavy). (6) *Content vs format*
— `locality0-provenance`: the canonical-order content hash is unmoved while the storage layout moves (the text-reformat
law for the tile). (7) *GAUNTLET-2 baseline* — the accepted single-thread emit p99 is sealed as the hard baseline the
parallel rung must beat; emit stays embarrassingly parallel (per-column wall, per-row floor).

**Three exits, ratified before the number.** Blocked wins, Morton wins, or **neither** beats the baseline — the last
is not a null but a proof the tile-fetch stall is a capacity/LRU miss no permutation of the 192 KB tile can fix,
redirecting the trajectory to `GAUNTLET-2` (parallelism) to hide the latency behind compute.

**Rows.** `locality0-preregistered` — the method, the process-isolation boundary, the three exits and the GAUNTLET-2
baseline are hash-locked (`28a9d792`). `locality0-equiv` — both layouts byte-identical over 19 cases + the non-vacuous
synthetic render. `locality0-bijection` — both swizzles are lossless bijections, proven on distinct data where a
collision would show. `locality0-provenance` — content unmoved, format moved. `locality0-indextax` — the deterministic
per-band within-cache-line locality (the shear story): on the witness, linear near/mid/far **153/534/714** permille →
blocked **845/941/964**, morton **738/883/928**; both raise locality in every band, most in the near-field where the
linear order scatters.

**Grade.** MEASURED (live, headless, deterministic): byte-identity of both layouts over corpus + adversarial cameras
(and the non-vacuous synthetic guard), the bijections, the content/format separation, and the per-band structural
locality. DECLARED: the hash-locked method + three exits. NOT_MEASURED here: which layout wins on the clock — that is
LOCALITY-0's process-isolated host court (`verify/locality0.py`), sealed off-gate, the promotion the reader's from the
three exits.

**does_not_show.** Which layout is faster (the gate carries no wall-clock; the host record does, off-gate). Any
comparison to GAUNTLET-0's instrumented absolute. That instruction-level invariance is proven (only output byte-identity
is; the address-generation isolation is best-effort code structure — the record says so). That the per-band locality is
a wall-clock (it is a deterministic proxy; the per-band µs are the host's). That the swizzle changed the content (it is
a pure re-format; the content provenance is unmoved).

**Falsifier.** `locality0-equiv` reddens if either layout differs from the frozen emit on any case or on the synthetic
distinct-per-texel render; `locality0-bijection` if a swizzle is not lossless on distinct data or is a byte-level no-op;
`locality0-provenance` if the content hash moves or the format does not; `locality0-indextax` if a layout fails to raise
locality over linear in any band; `locality0-preregistered` if the method, the isolation boundary or the three exits are
weakened.

## LOCALITY-0 LOCK — blocked promoted to the accepted single-thread emit; GAUNTLET-2's baseline sealed (seat 19)

**What landed (the court's consequence, made the production path).** LOCALITY-0's process-isolated host court fired
**Exit 1 (blocked wins)** on `DANIELDILLBERG`: the 8×8 cache-blocked floor layout was byte-identical to the frozen
emit **and** faster than the linear-fetch DDA (**8185 → 7734 µs p99**, ~1.07×), and it carried the *lower* index-
arithmetic tax of the two layouts (blocked X **356** vs Morton **1040**) — Morton bought the same locality but its
bit-interleave ate the gain and it landed slower (8736 µs). Same content, same execution boundary, only the layout
moved, so the win is causal proof the tile fetch was the cost. This seat is the LOCK: `emit_swizzled<BLOCKED>` is
promoted to the accepted single-thread `fast::emit`, monomorphized completely.

**The promotion, kept pristine.** The floor tile is ingested and re-laid into the blocked execution format **once at
scene load** (`fast::blocked_floor`); the production `emit` then reads that pre-swizzled buffer in the hot path via
`floor_blocked` — a pure shift/mask index, no runtime layout branch, no generic `<LAYOUT>` toggle, never touching
`scene.floor`. The blocked index has **one definition repo-wide**: the court's `locality::swizzle_index::<BLOCKED>`
delegates to the production `floor_blocked`, so apparatus and promoted path can never disagree. The pre-LOCK linear-
fetch DDA is retained **verbatim** as `emit_linear` on the archive shelf beside `emit_collapse` — an immutable
**reference witness**: the historical courts (the GAUNTLET-1c fast-bench, RE-BREAKDOWN-1's ablation/structure, and
LOCALITY-0's own LINEAR anchor and DDA baseline) all measure against it, so the LOCK's win stays reproducible and
nothing dead or commented-out is left in the engine loop.

**The baseline, sealed.** The accepted blocked emit's process-isolated p99 — **7734 µs** on `DANIELDILLBERG` — is
sealed as GAUNTLET-2's **hard baseline**: the multi-threaded rung inherits it, never re-derives it, and must beat it
under **thread-count invariance** (byte-identical for every thread count P) to promote. Taking the earned 1.07×
into the parallel court, rather than discarding it, forces the parallel implementation to fight against our best
single-thread work. GAUNTLET-2's baseline was first sealed here (`5c3a5c30`); its full method is preregistered in the
next seat (`711cc1d4`) so the floor and the decision rule are fixed before the rung is built.

**Rows.** `locality0-lock` — the blocked production emit and the archived `emit_linear` reference are both byte-
identical to the frozen emit (and render the same picture). `locality0-lockfence` — the source-level proof: `emit`
takes the pre-swizzled blocked buffer, uses `floor_blocked` in the hot path, never reads `scene.floor` there, and
carries no layout toggle (monomorphized); `blocked_floor` builds the format once; `emit_linear` is the verbatim
linear-fetch reference. `gauntlet2-preregistered` — the inherited single-thread baseline, thread-count invariance
and the two-court rule are hash-locked (upgraded to the full partition-invariance method in the next seat, `711cc1d4`).
`gauntlet1-equiv` / `gauntlet1c-dda` now certify BOTH the blocked production emit and the linear reference over the
corpus + adversarial cameras.

**Grade.** MEASURED (live, headless, deterministic): byte-identity of the blocked production emit and the archived
linear reference over corpus + adversarial cameras; the source-level LOCK fence. DECLARED: the hash-locked GAUNTLET-2
baseline and method. The **which-layout-wins** and the **7734 µs** are the host record's (`verify/locality0.py`,
off-gate) — the gate carries no wall-clock.

**does_not_show.** The speed win itself (the gate proves only byte-identity; the host record carries the µs). That
the blocked layout removes the stall for *every* scene (it is the accepted emit on this corpus; capacity behaviour is
scene-dependent). Any comparison to GAUNTLET-0's instrumented absolute.

**Falsifier.** `locality0-lock` reddens if the blocked emit or the archived reference drifts from the frozen emit;
`locality0-lockfence` if the production emit reads `scene.floor`, drops `floor_blocked`, grows a layout toggle, or the
archived `emit_linear`/`blocked_floor` go missing; `gauntlet2-preregistered` if the inherited-baseline rule, the
thread-count invariance or the two-court separation is weakened.

## GAUNTLET-2 — preregistered: partition invariance before parallelism (method locked, seat pending)

**What is locked (the method, before a line of implementation or a single number).** GAUNTLET-2 is opened but not yet
seated: the parallel emit does not exist, and no host number has been taken. What is sealed here is the *method*, so the
decision rule is fixed before any result can tempt it. The framing is deliberate — GAUNTLET-2 is **not** "make emit
multithreaded." It establishes the stronger property:

> **Partitioning the column domain changes execution parallelism but not the certified picture.** `emit` over any
> partition of the columns into groups, processed in any order, across any admitted thread count `T`, is byte-identical
> to the frozen emit. Thread count and column partition are **execution parameters, not rendering authority.**

**Two courts (the GAUNTLET separation, kept).** *Correctness* is deterministic and gate-enforced: a partition-agnostic
emit must reproduce the frozen `frame_digest` **and** `pixel_sha` for every tested column partition — contiguous chunks
at `T ∈ {1,2,4,8,16}` **and** adversarial partitions (strided/interleaved column assignment, reversed processing order,
single-column groups, a seeded permutation) — over the corpus plus adversarial cameras. The dangerous failure is no
longer arithmetic; it is an accidental dependency on shared framebuffer state, shared temporary state, mutable
material-lookup state, column ordering, thread-local initialization, or reduction/merge ordering — each of which shows
up as *partition-dependence*, caught deterministically without spawning a thread. *Performance* is host, off-gate: a
`std::thread` emit (no crates) partitions the columns across an **explicit** thread count `T` that is an input to the
benchmark and **recorded in the attestation** (a `T | correctness | p99` matrix), byte-identity checked before any
number, p99 compared **only** against the sealed single-thread baseline (never GAUNTLET-0's absolute, never the frozen
renderer, never an absolute refresh-rate claim).

**The decision rule, preregistered before the number.** Promote the parallel emit iff it is byte-invariant across every
admitted `(T, partition)` **and** some admitted `T > 1` has p99 below the sealed **7734 µs** baseline. And a subtle
consequence of the locality work: if p99 stops improving as `T` grows (sublinear or negative scaling), that is itself
evidence — of **memory-bandwidth / cache contention**, not insufficient parallelism — and the trajectory turns to the
memory hierarchy rather than blindly increasing `T`. The staircase reads `GAUNTLET-1c → LOCALITY-0 → GAUNTLET-2`:
*projection arithmetic → data locality → parallel execution*.

**Row.** `gauntlet2-preregistered` — the partition-invariance law, the adversarial-partition requirement, the explicit
thread-count-in-attestation, the two-court separation, the inherited (never re-measured) baseline and the decision rule
(including the memory-hierarchy redirect) are hash-locked (`711cc1d4`, superseding patch 0028's baseline-seal `5c3a5c30`
— no record cited it and the instrument has not run). **Grade.** DECLARED (the method; the correctness and performance
courts are the next builds). **Falsifier.** `gauntlet2-preregistered` reddens if the partition-invariance law, the
adversarial-partition or explicit-thread-count requirement, the two-court separation, or the decision rule is weakened.

## GAUNTLET-2 — the correctness court: partition invariance proven (seat 20)

**What landed (the stronger property, deterministically, with no threads).** GAUNTLET-2's correctness court is seated:
`kernel/fast.rs::emit_partitioned(group)` is a partition-agnostic sibling of the LOCKED emit. It renders exactly the
pixels of the columns in `group` — any subset, in any order — byte-identically to the frozen picture: ceiling + wall
per column as the frozen transcription, and the floor via the LOCKED blocked DDA **seeded per contiguous run** (the
DDA's `q` at column c is a pure function of c and kk, so a run seeded at any `lo` is exact). A contiguous group is one
full-DDA run — what the parallel court's threads will use; an adversarial group degrades to short runs but stays
byte-identical. The output is a pure function of the column **set**: disjoint per-column writes, no shared, accumulated
or reduction state, so over any partition of `0..W`, in any order, the framebuffer equals the frozen picture.

**T is not authoritative inside the kernel.** The kernel receives the actual column **groups**; the thread count `T`
only *generates* a partition spec in the harness (`main.rs --gauntlet2`). That makes the law testable independently of
any threading concept: `partition spec → emit_partitioned(groups) → framebuffer`, never `T → kernel decides partition`.

**The dangerous failures, caught without a thread.** The court runs ten partition specs over the corpus + adversarial
cameras: contiguous chunks at `T ∈ {1,2,4,8,16}`, strided/interleaved assignment, reversed group **and** within-group
column order, single-column groups (1920 of them), and a seeded permutation. Each is verified a true partition of
`0..W` (coverage exactly once, into a sentinel-filled buffer so a missed column would diverge) and byte-identical to
the frozen picture. An accidental dependency on shared framebuffer or temporary or material state, on column ordering,
thread-local init, or reduction/merge ordering would surface as *partition-dependence* and redden the gate —
deterministically, reproducibly, before a single `std::thread` exists.

**Rows.** `gauntlet2-partition-invariance` — all ten specs byte-identical to frozen over the corpus + adversarial
cameras, each a true partition, and the core at `T=1` equals the LOCKED blocked emit (`g2_vs_emit OK`), so no new
correctness surface was introduced. `gauntlet2-partition-fence` — `emit_partitioned` uses the LOCKED `floor_blocked` +
the pre-swizzled floor (never `scene.floor`), references no probe, and `fast.rs` contains **no** `std::thread`: this
patch commits partition invariance only, no parallel execution.

**Grade.** MEASURED (live, headless, deterministic): partition invariance of `emit_partitioned` over contiguous and
adversarial partitions, corpus + adversarial cameras, and equality with the LOCKED emit at `T=1`. NOT_MEASURED here:
any wall-clock — GAUNTLET-2's performance court (the `std::thread` emit and the `T | correctness | p99` matrix vs the
sealed 7734 µs) is the next build, off-gate.

**does_not_show.** Any speed (the correctness court carries no threads and no clock). That parallel execution beats the
baseline (the host performance court decides that). That partition invariance holds for scenes outside the corpus.

**Falsifier.** `gauntlet2-partition-invariance` reddens if any partition spec (contiguous or adversarial) diverges from
the frozen picture on any case, fails coverage, or if the `T=1` core diverges from the LOCKED emit.

## GAUNTLET-2 — the performance court: parallel execution, correctness gate-enforced first (seat 21)

**What landed (execution only, over an already-proven core).** GAUNTLET-2's performance court adds the parallel
execution mechanism and nothing else. `kernel/fast.rs::emit_threaded(threads)` builds the same contiguous column
partition the correctness court accepts (`T` contiguous groups over `0..W`) and calls the proven `emit_partitioned`
once per group across `std::thread::scope` — one contiguous group per thread, writing **disjoint** columns. It holds no
coordinate, material or pixel algorithm of its own; every pixel is routed through `emit_partitioned`. Because the output
is a pure function of the column set, it is byte-identical to the frozen picture at every thread count regardless of how
the threads are scheduled.

**Correctness is gate-enforced first; speed is off-gate.** `--gauntlet2-threads` renders `emit_threaded` at
`T ∈ {1,2,4,8,16}` into a sentinel-filled buffer and checks byte-identity to the frozen picture; the output is
deterministic though scheduling is not, so this is a legitimate, reproducible gate check that fires **before** any
performance interpretation. The wall-clock lives entirely off-gate: `--gauntlet2-bench N --threads T` times one
explicit thread count per process, byte-identity checked first, and `verify/gauntlet2.py` interleaves the thread counts
across strips (drift cancels) into the `T | correctness | p99` matrix, sealed under RECORD-0 to
`kernel/attest/gauntlet2-<host>.json`.

**The baseline is inherited, the decision rule preregistered.** The single-thread floor is read from the sealed
LOCALITY-0 record (`gauntlet2_baseline_p99_us`, **7734 µs** on `DANIELDILLBERG`) — inherited, never re-derived; the
orchestrator refuses to run without it. Promotion is exactly the preregistered rule: byte-invariant at every `T` **and**
some `T > 1` p99 below the baseline. And the memory-hierarchy redirect is honoured: if p99 stops improving as `T` grows,
the reading names it **memory-bandwidth / cache contention**, not insufficient parallelism, and points the trajectory at
the memory hierarchy rather than a bigger thread count. Never compared to GAUNTLET-0's absolute; no refresh claim.

**Rows.** `gauntlet2-threaded-equiv` — `emit_threaded` byte-identical to the frozen picture at every `T ∈ {1,2,4,8,16}`
over the corpus + adversarial cameras. `gauntlet2-threaded-fence` — `emit_partitioned` stays the clean core (LOCKED
`floor_blocked` + the pre-swizzled floor, never `scene.floor`, no probe), and `emit_threaded` routes every pixel through
`emit_partitioned` via `std::thread::scope` with no duplicate-renderer primitive. This row **replaces** the retired
`gauntlet2-partition-fence`, whose "no threading yet" job (proving seat 20 stayed correctness-only) is finished.

**Grade.** MEASURED (live, headless, deterministic): the threaded emit's byte-identity at every `T` and the
execution-only structure. NOT_MEASURED here: the parallel speed — the `T | correctness | p99` matrix vs the sealed
7734 µs is the host court (`verify/gauntlet2.py`, off-gate), which the owner runs on `DANIELDILLBERG`; the promotion is
the reader's from that matrix and the preregistered rule.

**does_not_show.** Any wall-clock on the gate. That parallelism beats the baseline (the host matrix decides, against the
inherited floor). Any refresh-rate or input-to-photon claim. Any comparison to GAUNTLET-0's instrumented absolute.

**Falsifier.** `gauntlet2-threaded-equiv` reddens if the threaded emit diverges from the frozen picture at any `T` on
any case (a partition/order or race dependency); `gauntlet2-threaded-fence` if `emit_partitioned` loses `floor_blocked`
or reads `scene.floor` or references a probe, or if `emit_threaded` acquires a second renderer (a coordinate/material/
pixel primitive) instead of routing through `emit_partitioned`.

## GAUNTLET-2 LOCK — the threaded emit adopted, T=8 the production default (seat 22)

**What landed (promotion, on a reproduced verdict).** The host performance court fired **PROMOTE** on `DANIELDILLBERG`,
and the shape was confirmed on a second independent sweep. The threaded emit is adopted: `kernel/fast.rs::render` is the
accepted production fast path — mantle's frozen strips + frame (the oracle's geometry, unchanged), then the pixels via
`emit_threaded` at `PROD_THREADS = 8` — and the shell's production render (`shell/present.rs::compose_frame`) is rewired
to call it, so the parallel headroom actually reaches the frame the window shows. Byte-identity is gate-enforced
(`gauntlet2-lock`: the production render reproduces the frozen picture's frame digest AND pixel sha over corpus +
adversarial cameras); the single-thread `emit`/`emit_linear` are retained as the reference witnesses.

**The measured facts (two sweeps, `DANIELDILLBERG`).** Every `T>1` beat the inherited **7,734 µs** single-thread
baseline in both runs. The matrix (run 1 / run 2, µs p99): T1 5019/5067, T2 3752/3923, T4 3012/2929, T8 **2360/2355**,
T16 **2311/2208**. T=16 was the measured-fastest both times (~3.35–3.50× over baseline); T=8 was the **stable knee** —
0.2% run-to-run — while T=16 carried 4.5% run-to-run variance. T=8 is ~3.27–3.28× over baseline.

**Why T=8 is the production default (and the honest grade of the plateau).** T=8 is chosen for a **deterministic**
production p99: it banks a rock-stable ~3.3× (2355–2360 µs, sub-1% run-to-run) rather than T=16's marginally-faster but
noisier point. The `T≥8` plateau and the elevated `T=16` variance are **consistent with** LOCALITY-0's memory-bound
finding — the emit is bandwidth-limited, so past ~8 threads the cores contend for memory rather than doing independent
work. That is graded as a **hypothesis supported by the run-to-run variance, NOT a direct bandwidth measurement**: this
court did not measure the memory bus, and it does not establish that exactly eight threads is the hardware's saturation
point. T=8 is an **execution parameter**, not rendering authority: the `{1,2,4,8,16}` partition/thread court
(`gauntlet2-threaded-equiv`) stays intact as the correctness oracle, unchanged by the choice of production `T`.
Recorded engineering facts: default T=8; tested ceiling T=16; T=16 measured-fastest in both sweeps; T=8 the selected
deterministic production default; T=16 the observed performance-ceiling / plateau candidate.

**Reproducibility, kept durable without clobbering.** The sealed measurement (`kernel/attest/gauntlet2-<host>.json`,
run 1) stays the canonical record. A confirming sweep is sealed SEPARATELY by `verify/gauntlet2.py --confirm` to
`kernel/attest/gauntlet2-confirm-<host>.json`, which cites the canonical record's chain hash and states whether the
shape reproduced — the second run's value is durable evidence, never a silent replacement of the original sealed number.

**Rows.** `gauntlet2-lock` — `fast::render` (production render, T=8) byte-identical to the frozen picture over corpus +
adversarial cameras; `render_threads == 8`. `gauntlet2-lockfence` — the structural LOCK: `fast::render` routes the
pixels through `emit_threaded` at `PROD_THREADS = 8` (no duplicate renderer), the shell's `present.rs` is wired to
`fast::render` and no longer calls the frozen `picture()` for its pixels, and the single-thread reference is retained.

**Grade.** MEASURED (host, off-gate, two sweeps): the p99 matrix and the ~3.3× promotion, reproduced. MEASURED (gate):
the production render's byte-identity at T=8 and the structural LOCK. HYPOTHESIS (evidence-supported, not established):
that the `T≥8` plateau is memory-bandwidth saturation — the variance is evidence, a bus measurement would be proof.
DECLARED: T=8 as the production default.

**does_not_show.** That eight threads is the exact bandwidth-saturation point (not measured). Any frame-rate,
refresh, or input-to-photon claim (this is emit p99, not the present path — that is LATENCY-1). Any comparison to
GAUNTLET-0's instrumented absolute. That the ~3.3× survives the frame-ready → composited path (LATENCY-1 measures that).

**Falsifier.** `gauntlet2-lock` reddens if the production render diverges from the frozen picture on any case or is not
at T=8; `gauntlet2-lockfence` if `fast::render` stops routing through `emit_threaded`/`PROD_THREADS`, if the shell's
production render reverts to the frozen `picture()`, if `PROD_THREADS != 8`, or if the single-thread reference is dropped.

## LATENCY-1 — preregistered: does the render headroom reach the screen (method locked, host-run pending)

**What is locked (the method, before any host number).** With the render now ~3.3× faster and the shell rendering
through the LOCKED T=8 path, `LATENCY-1` asks the question the whole GAUNTLET-2 campaign was ultimately for — **does
that render headroom survive the frame-ready → composited path?** It is a *measurement, not an optimization*: it does
not ask whether rendering is faster (established) but whether replacing the renderer with the promoted T=8 path
*measurably changes* the present-path latency of the fixed sealed session versus `LATENCY-0`'s sealed baseline.

**The comparator discipline (the reason to lock it first).** The comparison is drawn ONLY against `LATENCY-0`'s sealed
**frame-ready → composited** p99 — the *same observable* — inherited from `shell/attest/latency-<host>.json` and never
re-derived. It is **never** compared against an *emit* p99: the GAUNTLET-2 **7,734 µs** baseline is an emit-phase
time, a *different observable* from a present-path time, and mixing them is a category error. Locking this in
`preregister.json` (`8e93118e`) before the number means the mistake cannot be made silently.

**The disciplined reading, ratified before the result.** An *improvement* means the renderer headroom is propagating
into the measured presentation path; *no material improvement* means presentation/DWM remains the dominant measured
boundary (and `PRESENT-1` — a flip-model / waitable-swapchain path — becomes the next falsifiable hypothesis); a
*degradation* means the threaded path introduced a scheduling/contention cost at the shell boundary. None of these,
by itself, proves input-to-photon latency — that needs capture hardware and is out of scope.

**Instrument.** `shell/win32.rs playback_window --measure` (off-gate, host, `--cfg shell_window`), now rendering
through `fast::render` (T=8) via `present.rs`; sealed by `verify/latency1.py` → `shell/attest/latency1-<host>.json`,
citing this entry and inheriting the `LATENCY-0` baseline. **Row.** `latency1-preregistered` locks the method, the
same-observable comparator, the inherited baseline and the disciplined reading (`8e93118e`). **Grade.** DECLARED (the
method; the host measurement and its sealer are the next build). **Falsifier.** `latency1-preregistered` reddens if
the comparator, the inherited-baseline rule, the disciplined reading, the not-input-to-photon scope, or the
same-apparatus requirement is weakened.

*Cheap prerequisite measurement (existing instrument, no new rung): re-establish the post-optimization render phase
balance (`GHOSTS.md` G8). Note that `--breakdown` as it stands times the FROZEN `emit`; the honest G8 answer combines
its (unchanged) `strips`/`frame` phases with the FAST emit on one apparatus — a small `--breakdown` extension, not a
new rung. Privileged slices `BANDWIDTH-0` (G2) and `POOL-0` (G1/G3) remain uncommitted pending the `LATENCY-1` result.*

## GAME-0 — Urðr's game layer carried as frozen evidence, from the same tag (seat 23)

**What landed.** `oracle/game/` holds the runtime closure of Urðr's seventeen discrete game-layer vertical slices —
`gamegen`, `descent`, `move`, `entity`, `rngstream`, `descend`, `loot`, `combat`, `heirloom`, `actionlog`, `savegame`,
`enact`, `rerun`, `statecanon`, `kinema`, `chorus`, `cue` — with each slice's frozen conformance corpus, its red-first
suite and its brief, the `D24` game boundary and `D25` kinema boundary, the game-layer roadmap, and the two physics
modules `kinema` needs (`field.py` for the frozen Q32.32 radix, `rational.py` beneath it): 73 files, verbatim from
`urdr-oracle-1` at the same paths they have in Urðr. The closure was found by relocation, not by reading imports: the
slices were copied out of Urðr and their mains and suites run until nothing was missing, which surfaced three members an
import graph misses (`enact` reads the source of `combat` and `heirloom`; `test_cue` audits `chorus`).

**Why this is charter-clean.** These are CORE and VIEW semantics earned in Urðr and frozen at the tag the oracle
already cites. Carrying them is the charter's own route for CORE semantics; no new oracle is minted, no charter clause
moves, and no Verðandi code computes, edits or depends on them.

**Provenance a stranger can check.** `oracle/game/MANIFEST.json` lists every file's size, sha256 and **git blob id**
— the id `git ls-tree -r urdr-oracle-1` names at that path in Urðr — so each file can be checked against Urðr without
trusting this repository. Before import, all 73 staged files were hashed with `git hash-object` and matched their tag
blobs exactly (no line-ending drift); `.gitattributes` now marks the folder `-text` so git never rewrites one.

**Rows.** `game-frozen` — bytes, sha256 and git blob recomputed from disk equal the manifest for every file, the tree
holds nothing unlisted, the manifest's digest is pinned in the gate source, the origin is the oracle's tag and commit,
and every import is a closure module or one of nine pinned stdlib names. `game-suites` — Urðr's own 411 tests pass in
place under `PYTHONHASHSEED=0` (conformance goldens included) and all seventeen slices' witnesses exit 0 and print
their `does_not_show`. `game-plant` — one hex digit of `move`'s frozen `move-digest` golden, flipped in a scratch copy,
is refused by the byte check and reddens `test_move`. `game-not-runtime` — no `kernel/`, `workshop/` or `shell/` code
reaches into `oracle/game` (the charter's ORACLE clause), with planted references proving the scan sees one.

**Grade.** ESTABLISHED (gate): the import is byte-exact against the tag's blobs, self-contained, and passes Urðr's own
suites in place. DECLARED: the closure's completeness beyond what the relocation run exercised.

**does_not_show.** Any Verðandi-native placement of a game slice (that would be a separate rung reproducing these
corpora, as `KERNEL-0` reproduced the renderer). Any coupling between the game layer and the renderer, the workshop or
the shell. Anything each slice's own `does_not_show` disclaims. That the rest of Urðr's `tools/physics` or its
`tools/netcode` is imported — it is not; only `field` and `rational` are here.

**Falsifier.** `game-frozen` reddens on any byte change, any added or missing file, a manifest edit that is not also a
gate-source edit, another origin, or an import outside the closure; `game-suites` if any of Urðr's tests fails, the count
is not 411, or a witness exits non-zero; `game-plant` if a flipped golden passes either check; `game-not-runtime` if
runtime code reaches into the folder.

## LATENCY-1a / LATENCY-1R — the instrument fact recorded before the number; the render put inside the clock (LATENCY-1 measured and confirmed; LATENCY-1R measured twice — reproduced in magnitude, the locked label flipped)

**What landed.** Two hash-locked preregistrations, the instrument for the second, and both host sealers — before any
LATENCY-1 or LATENCY-1R number exists.

**The instrument fact (LATENCY-1a, `b32d226f`).** Reading LATENCY-0's instrument before building LATENCY-1's sealer
showed that the preregistered LATENCY-1 cannot do what its three-way reading assumed. `shell playback-window` renders
every move of the sealed session (`playback::frames` → `compose_frame` → `fast::render`) **before** the window opens,
and `latency_measure` times frame-ready (QPC after `StretchDIBits`) → composited (QPC after `DwmFlush`) over those
pre-rendered bitmaps. The renderer is outside the clock, so a single-thread build and the T=8 build measure the same
interval up to noise, and LATENCY-1's "improvement = render headroom propagates" branch could never fire on the render.
That reading was written into LATENCY-1 (`8e93118e`) by this program and is corrected here rather than massaged. The
amendment cites LATENCY-1's current hash, alters none of its observable, comparator, session, apparatus or entry, and
binds how its delta is read: against a declared 50‰ materiality bound, **NO MATERIAL CHANGE** means the presentation
interval reproduces LATENCY-0 (the second-run shape confirmation LATENCY-0's own failure condition asks for), and a
material **IMPROVEMENT** or **DEGRADATION** is a change of the presentation interval itself — never render headroom
propagating, never render contention. The instrument writes to the sealed LATENCY-0 record's path, so the sealer
restores that record byte-exact before sealing.

**The render-inclusive court (LATENCY-1R, `5cfb3ece`).** A separate observable, preregistered as its own rung:
render-start → composited, per sample, on the same sealed session and the same GDI present. Two arms render the
identical certified frame and differ only in the pixel pass — **production** (`fast::render`, `emit_threaded` at
`PROD_THREADS = 8`) and the **single-thread reference** (the LOCKED `fast::emit`). The render's phase against
composition is a declared variable: **locked** (the render starts right after a composition) and **uniform** (at a
seeded offset uniform in [0, refresh) after one, seed `0x5EED1A7E00000001`). Witnesses come first — both arms reproduce
every sealed frame witness and each other's composites before any clock — then N samples per cell, ABBA-interleaved,
each starting from a composition, with a byte-for-byte drift check after each sample, outside the interval. Per
regime, on p50s: render delta dR = render(S) − render(P), glass delta dG = total(S) − total(P), propagation =
⌊1000·dG/dR⌋‰ → **PROPAGATES** (≥ 500), **PARTIALLY ABSORBED** (1–499), **ABSORBED** (≤ 0), **VOID** (dR ≤ 0: no
headroom in this apparatus). p99s are reported beside it and never folded in. LATENCY-0's refresh coupling predicts
absorption in the locked regime and near-full propagation in the uniform one — to be measured, not assumed.

**The instrument.** `shell/latency1r.rs` is the court, platform-agnostic, over a `Surface` (clock, present,
composition barrier, pump). On the host it runs over a GDI surface **appended** to `shell/win32.rs` after LATENCY-0's
instrument, whose text stays a byte-exact prefix of the file; its present mirrors LATENCY-0's `present_once` exactly.
On the gate the same court runs over a deterministic mock surface (`shell latency1r-selftest`). The window build was
type-checked in the container (`--emit=metadata`, the window cfg on); linking and running are the host's.
`verify/latency1.py` and `verify/latency1r.py` seal `shell/attest/latency1-<host>.json` and
`shell/attest/latency1r-<host>.json`; `--confirm` seals a separate confirmation record beside each.

**Rows.** `latency1a-preregistered` — the amendment is locked, cites LATENCY-1's current hash, and its instrument
fact is checked **in source** (the playback-window dispatch pre-renders; `latency_measure` holds no render call).
`latency1r-preregistered` — the 1R method is locked and the code's seed and thresholds equal the registered ones.
`latency1-sealers` — both sealers driven with synthetic numbers: court A's three categories fire at the 50‰ bound and
every reading is bound by the amendment, a different session / partial run / baseline not citing LATENCY-0 is refused,
and the LATENCY-0 record is restored byte-exact even when the instrument fails; court B's four readings fire at the
registered thresholds and a record with another seed or production T is refused. `latency1r-court` — the court runs
headless over the mock on the sealed session (witnesses first, 4 cells, the locked regime quantized and the uniform
one offset), its raw record seals and reads VOID (the mock has no render headroom); plants: a tampered witness and a
mid-court close both refuse with no record. `latency1r-fence` — LATENCY-0's instrument is a byte-exact prefix of
`win32.rs`, `playback::frames` and the playback-window dispatch are unchanged, the arms differ only in the pixel pass,
and the court orders witnesses → refresh → t0 → render → present → drift check with no hashing inside the clock.

**LATENCY-1 measured (host DANIELDILLBERG, `shell/attest/latency1-DANIELDILLBERG.json`, cites LATENCY-1 `8e93118e` +
LATENCY-1a `b32d226f`, inherits LATENCY-0).** 200 samples over the 4-move sealed session: blit → composited **p50 5,965
/ p95 6,882 / p99 12,299 / max 20,140 µs**, measured refresh 13,089 µs. Against the inherited LATENCY-0 p99 of 7,318 µs
the locked rule read **DEGRADATION** (+4,981 µs, 680‰ ≥ 50‰), recorded as such. It was a tail, not a shift: p50 moved
+44 µs and p95 −196 µs, and with n = 200 the p99 is the third-largest sample, so three samples took ≥ 12.3 ms (about
one extra composition; the max about one and a half).

**The confirmation did not reproduce it (`shell/attest/latency1-confirm-DANIELDILLBERG.json`, cites the first record).**
The second run read **NO MATERIAL CHANGE**: **p50 5,703 / p95 6,890 / p99 7,339 / max 7,477 µs**, refresh 13,561 µs —
p99 within 21 µs (2‰) of LATENCY-0's 7,318. The confirmation record states that the shape did not reproduce. Across
the three runs of this instrument (LATENCY-0, LATENCY-1, its confirmation) the body is stable (p50 5.7–6.0 ms, p95
6.9–7.1 ms); the first LATENCY-1 run carried a three-sample tail the other two did not. The disciplined reading: the
presentation interval **reproduces LATENCY-0** — which is also the second run LATENCY-0's own failure condition asked
for — and the first run's DEGRADATION is a transient that a 200-sample p99 is thin enough to register (`GHOSTS.md`
G10). Per LATENCY-1a, none of it is about the renderer, which ran before the window opened. The sealed LATENCY-0
record was restored byte-exact both times.

**LATENCY-1R, first host attempt: refused, no record.** The window court stopped with `LATENCY1R-CLOSED` — the window
received a close before N samples per cell — and, as preregistered, wrote nothing. LATENCY-0's measurement loop only
leaves its message pump on a close and keeps measuring, so a close during a LATENCY-0/1 run is not detected there. The
court now reports where a close lands (round, samples taken), prints progress, and on a close reports whether the
window still existed and the last keyboard/mouse/system-command message the pump saw. None of this touches the timed
interval or LATENCY-0's instrument.

**LATENCY-1R measured (host DANIELDILLBERG, `shell/attest/latency1r-DANIELDILLBERG.json`, cites LATENCY-1R
`5cfb3ece`).** The second attempt ran to completion with no close: witnesses first, then 200 samples in each of four
cells, measured refresh 13,926 µs. Per cell, p50 / p99 in µs:

| regime | arm | render-start → frame-ready | frame-ready → composited | render-start → composited |
|---|---|---|---|---|
| locked | production (T=8) | 15,430 / 17,890 | 10,058 / 12,826 | **25,550** / 27,107 |
| locked | single-thread | 18,070 / 19,732 | 7,499 / 9,826 | **25,552** / 26,749 |
| uniform | production (T=8) | 14,826 / 17,327 | 6,780 / 14,050 | **21,400** / 29,004 |
| uniform | single-thread | 17,499 / 18,560 | 7,592 / 14,255 | **24,987** / 32,114 |

The preregistered rule, on p50s:

- **locked — ABSORBED.** Render delta dR = 2,640 µs, glass delta dG = 2 µs, 0‰. The production arm's frame-ready →
  composited grew by 2,559 µs, about the whole render saving: both arms land on the same composition, and the time
  the faster render saves is spent waiting for it.
- **uniform — PROPAGATES.** dR = 2,673 µs, dG = 3,587 µs, 1,341‰; the p99 total fell 3,110 µs. Composited output is
  3.6 ms earlier at the median (14% of the single-thread arm's 25.0 ms). Propagation above 1,000‰ is possible because
  composited times are quantized to compositions: a shorter render moves some samples a whole composition earlier,
  and medians do not subtract. That is the mechanism the numbers are consistent with, not a separate measurement.

What this answers (`GHOSTS.md` G7): GAUNTLET-2's render headroom **does** reach composited output for work that arrives
at a random phase (an input, say), and it **does not** for a loop that renders right after it presents, where the
refresh-coupled GDI present absorbs it. A second finding sits beside the verdicts. In this window the render-start →
frame-ready interval of the **production** arm is 15.4 ms at p50, longer than one refresh (13.9 ms). That interval
holds more than the renderer: mantle's strips and frame, the pixel pass, the HUD, the BGR conversion, and
`StretchDIBits`'s 2:1 downscale into the half-size client area (LATENCY-0's frame-ready excludes that blit; this
interval includes it). The two arms differ in it by only 2.6 ms, and how its ~15 ms divides among those phases
is not measured here. That split is the next cheap measurement (`GHOSTS.md` G8). The measured refresh moved
again (13,926 µs, 47‰ from LATENCY-0's); the 1R verdicts do not use it.

**LATENCY-1R confirmation (`shell/attest/latency1r-confirm-DANIELDILLBERG.json`, cites the first record).** A second
full run, no close, 200 samples per cell, measured refresh 13,433 µs. Per cell, p50 / p99 in µs:

| regime | arm | render-start → frame-ready | frame-ready → composited | render-start → composited |
|---|---|---|---|---|
| locked | production (T=8) | 15,669 / 18,468 | 9,992 / 12,440 | **25,563** / 26,864 |
| locked | single-thread | 18,463 / 21,204 | 7,108 / 9,234 | **25,587** / 26,519 |
| uniform | production (T=8) | 14,851 / 17,710 | 7,245 / 14,353 | **21,977** / 29,756 |
| uniform | single-thread | 17,591 / 21,287 | 7,289 / 14,266 | **25,217** / 32,348 |

- **uniform — PROPAGATES again.** dR = 2,740 µs, dG = 3,240 µs, 1,182‰ (the first run: 1,341‰). Composited output is
  3.2 ms earlier at p50 and 2.6 ms at p99. This regime reproduced, category and magnitude.
- **locked — PARTIALLY ABSORBED by the rule, absorbed in substance.** dR = 2,794 µs, dG = 24 µs, 8‰. The first run
  read ABSORBED (dG = 2 µs, 0‰). Both runs let less than 1% of the render saving reach composited output, and in both
  the production arm's frame-ready → composited grew by about the saving (2,559 and 2,884 µs); at p99 the production
  arm's total was slightly *later* both times (358 and 345 µs). But the preregistered boundary between ABSORBED (≤ 0‰)
  and PARTIALLY ABSORBED (1–499‰) has no margin, so a 22 µs difference moved the label. The confirmation record
  therefore states, correctly by the rule's letter, that the locked shape did **not** reproduce. The reading here is
  both at once: the label did not reproduce; the magnitude did. Changing the boundary would be a method change, to be
  preregistered before any further number and never applied to these two (`GHOSTS.md` G10).

**The status these two courts support.** Render-side: the T=8 production render shortens the shell's render-start →
frame-ready interval by 2.6–2.8 ms at p50 (about 15% of the single-thread arm's), in all four regime-runs. Screen-side:
that saving reaches composited output when the work arrives at an arbitrary phase (3.2–3.6 ms earlier at p50) and is
absorbed by the refresh-coupled GDI present when rendering starts right after a composition. The production
render-start → frame-ready interval is 14.8–15.7 ms at p50 across both runs and both regimes, longer than every refresh
estimate taken (13.1–13.9 ms), and its split is unmeasured. So: renderer latency materially improved; end-to-end
presentation latency phase-dependent; no low-latency or competitive claim made; the dominant whole-frame cost
unresolved. The next measurement is the split of that interval (`GHOSTS.md` G8), before any further optimization —
presentation or renderer.

**Grade.** DECLARED: both methods (hash-locked). ESTABLISHED (gate): the instrument fact in source; the sealers'
decision rules; the court's logic over the mock surface. MEASURED (host): LATENCY-1's presentation interval —
reproduces LATENCY-0 on confirmation, the first run's DEGRADATION not reproduced; LATENCY-1R, two runs — uniform
PROPAGATES (reproduced), locked absorbed in magnitude in both (< 1% propagated) with its label flipping ABSORBED →
PARTIALLY ABSORBED across a zero-margin boundary, and a production render-start → frame-ready interval longer than
every refresh estimate. Not MEASURED: how that interval divides among its phases.

**does_not_show.** Input-to-photon. Any comparison between LATENCY-1 and LATENCY-1R, or between either and an emit
p99. That the locked or uniform regime is a real game loop under load. How the ~15 ms render-start → frame-ready
interval divides among its phases. That the locked regime's category reproduces (its magnitude did; its label
did not). A low-latency or competitive-presentation claim of any kind.

**Falsifier.** `latency1a-preregistered` reddens if the amendment is edited, stops citing LATENCY-1's hash, or its
instrument fact becomes false in source; `latency1r-preregistered` if the method is weakened or the code's seed or
thresholds drift from it; `latency1-sealers` if a reading branch fires elsewhere than registered or attributes court
A's delta to the renderer; `latency1r-court` if a plant passes or the court's regimes stop behaving as declared;
`latency1r-fence` if LATENCY-0's instrument is edited or the court's ordering changes. On the host, a witness mismatch
or a closed window yields no number, and a shape that does not reproduce under `--confirm` refutes the reading.

## FRAME-SPLIT-0 — where the render-start → frame-ready interval goes (measured and confirmed: NO SEAT, multi-component)

**Why it is next.** LATENCY-1R measured the shell's render-start → frame-ready interval at 14.8–15.7 ms p50 for the
production render, longer than every refresh estimate on the owner's host, with the two arms differing in it by only
2.6–2.8 ms. The renderer's own latency is materially improved; the dominant whole-frame cost is unresolved. The next
rung is therefore a measurement, not an optimization: split that interval before choosing anything to change.

**The method (`739dc807`).** Seven contiguous phases, in order — **strips** (mantle's `Scene::strips`), **frame** (the
index-frame buffer allocated and `Scene::frame`), **floor_swizzle** (`fast::blocked_floor`), **emit** (the pixel buffer
allocated and the pixel pass: `emit_threaded` at `PROD_THREADS = 8`, or the LOCKED `fast::emit` for the single-thread
arm), **hud** (`hud::overlay`), **bgr** (`to_blit`) and **blit** (`GetDC` + `StretchDIBits`, ending at frame-ready, the
hard boundary). No variable is added to LATENCY-1R's apparatus: the same window and half-size client area, the same
sealed session, the same GDI present, the locked phase origin. Per arm, an uninstrumented **envelope** cell (the path
LATENCY-1R timed, no interior clock read — the accounting envelope) is interleaved ABBA with an instrumented **split**
cell (the same statements with a clock read after each phase), after 10 warm-up rounds, N samples per cell (default
300). Witnesses come first: every arm's envelope path reproduces every sealed frame witness, the marked mirror
reproduces it byte for byte, and the arms agree, before any clock. Frame-ready → composited is kept beside as an
anchor, not split.

**The reading, on the production arm** (the single-thread split is context and takes no seat). The instrumentation
tax is split total − envelope, at p50 and p99; |tax p50| ≥ 100‰ of the envelope p50 reads **VOID** (the probes perturbed
the interval too much to attribute it). Otherwise each phase's share is ⌊1000 · p99(phase) / p99(envelope)⌋ —
GAUNTLET-0's formula with the envelope as the denominator: exactly one phase ≥ 500‰ reads **SEAT** (the next target);
none reads **NO SEAT, multi-component** (no single phase is promoted); several reads **NO SEAT**, the several named and
none promoted. Reconciliation is reported and never distributed: a split's phases sum to its total per sample by
construction; the tax, and the sum of the phase p50s against the split total p50 (medians do not add), are recorded
as measured.

**The instrument.** `shell/framesplit.rs` is the court, platform-agnostic over LATENCY-1R's `Surface`; on the host it
runs over the same GDI surface, its window driver appended to `shell/win32.rs` after LATENCY-1R's (LATENCY-0's
instrument still a byte-exact prefix); on the gate over the mock surface (`shell framesplit-selftest`). The split's
path is `present.rs::arm_composite_marked`, which makes `fast::render`'s calls in `fast::render`'s order;
`fast::render` itself is untouched, and the envelope cells call it, so the mirror's cost difference is inside the
measured tax. The window build was type-checked here; linking and running are the host's. `verify/framesplit.py`
seals `shell/attest/framesplit-<host>.json`; `--confirm` seals a separate confirmation record beside it.

**Rows.** `framesplit-preregistered` — the method is locked and the code's phases, warm-up and thresholds equal the
registered ones. `framesplit-sealer` — synthetic splits: SEAT, NO SEAT (multi-component), NO SEAT (several) and VOID
fire at the registered bounds, shares use the envelope p99, the tax and the median gap are recorded, malformed records
are refused. `framesplit-court` — the court over the mock on the sealed session: witnesses first, the mirror byte-equal,
the warm-up, each split's phases summing exactly to its total, the raw record sealing (VOID under the mock, where the
probes are all the time there is); plants: a tampered witness and a mid-court close both refuse with no record.
`framesplit-fence` — the envelope calls `arm_composite`, the mirror follows `fast::render`'s call order with exactly
five marks, the timed interval is t0 → render → bgr → present with no hashing, and the window driver is appended
after LATENCY-1R's.

**Measured (host DANIELDILLBERG, `shell/attest/framesplit-DANIELDILLBERG.json`, cites FRAME-SPLIT-0 `739dc807`).**
300 samples per cell after 10 warm-up rounds, no close, measured refresh 13,363 µs. Production envelope render-start →
frame-ready **p50 15,690 / p99 17,863 µs** (single-thread 18,452 / 21,021). The split, in µs (p50 / p99) with each
phase's share of the envelope (p99 share, the seat rule's; p50 share beside it):

| phase | production (T=8) | p99 share | p50 share | single-thread | p99 share |
|---|---|---|---|---|---|
| strips | 62 / 170 | 9‰ | 3‰ | 62 / 156 | 7‰ |
| frame | 2,911 / 4,487 | 251‰ | 185‰ | 2,943 / 4,454 | 211‰ |
| floor_swizzle | 79 / 137 | 7‰ | 5‰ | 79 / 203 | 9‰ |
| emit | 3,566 / 4,869 | 272‰ | 227‰ | 6,828 / 7,734 | 367‰ |
| hud | 51 / 126 | 7‰ | 3‰ | 45 / 57 | 2‰ |
| bgr | 1,778 / 2,483 | 139‰ | 113‰ | 1,711 / 2,002 | 95‰ |
| **blit** | **7,087 / 7,762** | **434‰** | **451‰** | 7,063 / 8,111 | 385‰ |

**The reading: NO SEAT (multi-component).** No production phase reaches 500‰ of the envelope, at p99 or at p50, so
the court promotes no single optimization target — which is the outcome the rule was written to be able to give.
The largest phase is **blit** (`GetDC` + `StretchDIBits`, including the 2:1 downscale into the half-size client area):
434‰ at p99 and about 7.1 ms at p50, essentially the same in both arms. It is the largest component, not a seated
bottleneck. After it come **emit** (272‰; its phase includes the 6 MB pixel buffer's allocation) and **frame** (251‰;
including the 2 MB index buffer's allocation), then **bgr** (139‰). Grouped loosely, the two phases after the render
(bgr + blit) hold about 57% of the median envelope and the renderer's frame + emit about 41% — a grouping the
preregistration does not rule on and no seat follows from.

**Reconciliation, reported, not distributed.** The instrumentation tax is −154 µs at p50 (9‰ of the envelope, well
inside the 100‰ VOID bound) and −42 µs at p99; a negative tax is not a negative cost — envelope and split samples are
not paired, and scheduling and cache state move either median by that much. It is recorded as measured and no phase
is corrected by it. The production phase p50s sum to 15,534 µs against a split total of 15,536 µs (a 2 µs gap; for the
single-thread arm the gap is −228 µs, because medians do not add). The single-thread context confirms where GAUNTLET-2's
saving sits: emit p50 6,828 → 3,566 µs, with the other phases within ~70 µs between arms.

**Confirmed (`shell/attest/framesplit-confirm-DANIELDILLBERG.json`, cites the first record).** The preregistered second
run reads **NO SEAT (multi-component)** again, and the confirmation record states that the reading reproduced.
Production envelope p50 15,766 / p99 18,015 µs (the first run 15,690 / 17,863: +8‰ at p99). The p99 shares, first run →
confirmation:

| phase | strips | frame | floor_swizzle | emit | hud | bgr | blit |
|---|---|---|---|---|---|---|---|
| first run | 9‰ | 251‰ | 7‰ | 272‰ | 7‰ | 139‰ | 434‰ |
| confirmation | 9‰ | 259‰ | 10‰ | 269‰ | 7‰ | 136‰ | 427‰ |

Every share moved by 8‰ or less; the blit moved *away* from the 500‰ boundary (434 → 427‰), its p50 steady at ~7.1 ms
(7,087 → 7,082 µs). The instrumentation tax was −44 µs at p50 (2‰), again recorded and not used to correct any phase.
So the post-GAUNTLET-2 frame is confirmed multi-component: no single phase is promoted, the blit is the largest
component and not a bottleneck, and the next step is a narrower diagnostic of one named component — the destination
scaling inside the blit (PRESENT-SCALE-0 below) — rather than an optimization.

**Grade.** DECLARED: the method (hash-locked). ESTABLISHED (gate): the court's logic, the mirror's byte-identity and
call order, the sealer's rule. MEASURED (host, two runs): the split and its reading — NO SEAT, multi-component,
reproduced; the blit the largest phase at 427–434‰.

**does_not_show.** A split of the composition wait after frame-ready. How much of the blit is the 2:1 scaling rather
than the copy. What an optimization of any phase would achieve. That blit is "the bottleneck" (it did not seat). Any
other window size, phase origin or host. Input-to-photon.

**Falsifier.** `framesplit-preregistered` reddens if the method is weakened or the code drifts from it;
`framesplit-sealer` if a reading fires elsewhere than registered; `framesplit-court` if a plant passes or a split stops
summing to its total; `framesplit-fence` if the mirror leaves `fast::render`'s calls, the envelope stops being the
production path, or LATENCY-0's instrument is edited. On the host, a witness or mirror mismatch or a closed window
yields no number, a tax ≥ 100‰ refuses attribution, and a reading that does not reproduce under `--confirm` is
refuted.

## PRESENT-SCALE-0 — how much of the blit is the 2:1 destination scaling (a diagnostic; measured and confirmed: SCALING MATERIAL)

**Why it is next.** FRAME-SPLIT-0, confirmed, found the blit — `GetDC` + `StretchDIBits` of the 1920×1080 composite
into the half-size client area — the largest phase of the frame (~7.1 ms p50) without a seat, and `GHOSTS.md` G11 had
already recorded that what reaches the glass is GDI's 2:1 downscale of the certified picture. The narrowest next
question is how much of the blit that scaling is. This is a **diagnostic court**: it attributes; it does not seat,
promote a change, or name a winner.

**The method (`64b263da`).** One variable, the destination geometry, as a **client-area** size (never the outer window
size): **half** (960×540) against **full** (1920×1080, 1:1 with the source). Everything else is FRAME-SPLIT-0's
production path unchanged — the same sealed session, the envelope (`arm_composite`) and split
(`arm_composite_marked`), the same HUD and BGR buffer, the same GDI present, the locked phase origin. The window is
resized between **blocks**, never between samples: 8 blocks, H F F H H F F H, each opening with 5 discarded warm-up
rounds; after every resize the client rectangle is read back and must equal the request, or the court refuses. Per
geometry the envelope and the split are recorded, so a geometry that silently changed the rest of the frame is caught.
The logical and physical screen sizes and the device context's stretch mode are recorded, never varied. The outcome is
not predicted: a 1:1 destination skips the scaling but writes four times the destination pixels.

**The reading, on p50s.** **VOID** if either geometry's |instrumentation tax| ≥ 100‰ of its envelope. **CONFOUNDED** if the
six non-blit phases, summed, moved ≥ 50‰ of their half-size sum (the geometry changed more than the blit; nothing is
attributed to scaling). Otherwise, with dB = blit(full) − blit(half): |dB| ≥ 100‰ of blit(half) reads **SCALING
MATERIAL** (the sign says whether the full-size, unscaled destination was cheaper or dearer), and anything less reads
**SCALING IMMATERIAL**. p99s, both envelopes and frame-ready → composited are reported beside, never folded in.

**The instrument.** `shell/presentscale.rs` is the court, generic over a `GeomSurface` (a `Surface` whose client area
can be set). On the host it runs over a GDI surface appended to `shell/win32.rs` after FRAME-SPLIT-0's driver: the
client area is sized through `AdjustWindowRect` + `SetWindowPos` at a fixed position and read back with
`GetClientRect`, and its present mirrors LATENCY-0's `present_once` with the destination rectangle as the only change.
Its window procedure is LATENCY-0's plus `WM_GETMINMAXINFO`, which raises the maximum tracking size so a full client
area is not clamped to the screen. On the gate the court runs over the mock surface (`shell presentscale-selftest`).
The window build was type-checked here; linking and running are the host's. `verify/presentscale.py` seals
`shell/attest/presentscale-<host>.json`; `--confirm` seals a separate confirmation record beside it.

**Rows.** `presentscale-preregistered` — the method is locked and the code's geometries, block order, warm-up and
thresholds equal the registered ones. `presentscale-sealer` — synthetic geometries: SCALING MATERIAL (both signs, at
exactly 100‰), SCALING IMMATERIAL (99‰), CONFOUNDED (50‰) and VOID fire at the registered bounds; a clamped client
area, another block order or another source size is refused. `presentscale-court` — the court over the mock on the
sealed session: witnesses first, 8 blocks with the client area verified, both geometries recorded, each split summing
to its total; plants: a tampered witness, a window manager that clamps the full client area, and a mid-court close all
refuse with no record. `presentscale-fence` — the present differs from LATENCY-0's only in the destination rectangle,
the client area is sized at a fixed position and read back, the window style and procedure are LATENCY-0's (plus
`WM_GETMINMAXINFO`), the court uses FRAME-SPLIT-0's envelope and split paths, resizes only between blocks and hashes
nothing inside the interval, and LATENCY-0's instrument is still a byte-exact prefix.

**Measured (host DANIELDILLBERG, `shell/attest/presentscale-DANIELDILLBERG.json`, cites PRESENT-SCALE-0 `64b263da`).**
300 samples per cell over 8 blocks, no close; both client areas read back exactly as requested (960×540 and
1920×1080); logical screen = physical desktop = 1920×1080 (no display scaling); the device context's stretch mode
**1 (`BLACKONWHITE`)**; measured refresh 13,163 µs. p50 / p99 in µs:

| | half (960×540) | full (1920×1080) | full − half |
|---|---|---|---|
| **blit** | **7,755 / 8,410** | **2,194 / 2,756** | **−5,561 / −5,654** |
| non-blit phases, p50 sum | 9,538 | 9,078 | −460 (48‰) |
| envelope render-start → frame-ready | 17,098 / 19,508 | 11,395 / 13,365 | −5,703 / −6,143 |
| frame-ready → composited | 8,476 / 12,331 | 5,176 / 15,331 | −3,300 / +3,000 |

**The reading: SCALING MATERIAL (the full-size destination is cheaper).** The blit's p50 fell by 5,561 µs — 717‰ of the
half-size blit, far past the 100‰ bound — while the six non-blit phases moved 460 µs (48‰), just inside the 50‰
CONFOUNDED bound, and the instrumentation tax stayed inside the VOID bound in both geometries. So destination
geometry materially changes the GDI blit on this host, in the cheaper direction: on this host, in this exact GDI
apparatus and workload, the 1:1 destination configuration had a far lower blit p50 than the 2:1 `BLACKONWHITE`
configuration. That is not a general statement about GDI or Windows, whose stretching behaviour depends on the mode
and the configuration. The number is the preregistered **net** — the scaling removed and the larger copy added — not
the scaler's own cost. About 97% of the
envelope's median drop (5.7 ms, 333‰) is the blit.

**Beside the reading, not ruled on.** At full size the envelope p50 (11.4 ms) is below the measured refresh (13.2 ms)
and its p99 (13.4 ms) about at it; at half size both are well above it. frame-ready → composited moved the other way at
the tail: its p50 fell 3.3 ms (the frame now finishes before the next composition) but its p99 rose 3.0 ms, so the blit
result is not an end-to-end latency result. The non-blit movement (48‰) sits close to the confound bound, which is
why the rule has one. On this 1920×1080 screen the full-size client area extends below the screen edge (its title bar
takes the top rows); the blit writes all of it. Stretch mode 1 is `BLACKONWHITE`, which combines the pixels a 2:1
reduction eliminates with a Boolean AND rather than averaging them ([MS-WMF StretchMode](https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-wmf/b839b18a-a47c-4a44-b365-ef17d3c89e9a)) —
what the shell's half-size window has been showing is that reduction of the certified picture (`GHOSTS.md` G11).
Finally, the half-size condition here read slower than FRAME-SPLIT-0's window (envelope p50 17.1 vs 15.7–15.8 ms): the
client area is now set exactly and the blocks alternate with full-size ones. That is a cross-court difference neither
rule covers; it is recorded, not interpreted, and the within-court comparison (block-ABBA) is what the reading uses.

**Confirmed (`shell/attest/presentscale-confirm-DANIELDILLBERG.json`, cites the first record).** The preregistered
second run reads **SCALING MATERIAL (the full-size destination is cheaper)** again, and the confirmation record states
that the reading reproduced. The same stretch mode (1) and screen, refresh 13,394 µs. p50 / p99 in µs:

| | half (960×540) | full (1920×1080) | full − half |
|---|---|---|---|
| **blit** | **7,461 / 8,547** | **2,199 / 2,830** | **−5,262 / −5,717** |
| non-blit phases, p50 sum | 9,429 | 9,115 | −314 (33‰) |
| envelope render-start → frame-ready | 16,959 / 19,683 | 11,243 / 13,506 | −5,716 / −6,177 |
| frame-ready → composited | 8,557 / 12,280 | 3,637 / 15,252 | −4,920 / +2,972 |

The blit delta was 705‰ of the half-size blit (the first run: 717‰), the full-size blit steady at ~2.2 ms, and the
non-blit movement smaller this time (33‰ against 48‰), further from the confound bound. The tail pattern reproduced
too: frame-ready → composited p99 rose ~3.0 ms at full size in both runs while its p50 fell, so the blit result is still
not an end-to-end latency result. At full size the envelope p50 (11.2 ms) was again below the measured refresh.

**Grade.** DECLARED: the method (hash-locked). ESTABLISHED (gate): the court's logic, the geometry refusal, the
sealer's rule. MEASURED (host, two runs): SCALING MATERIAL, the full-size destination cheaper, net −5.26 to −5.56 ms at
the blit's p50 — reproduced, on this host and apparatus.

**does_not_show.** That the shell should present at full size, or with any other stretch mode — each would be a
separate court, because it changes what the window shows. Anything about a
present path other than `StretchDIBits` into a GDI window (PRESENT-1's flip model is not measured). That the pixels on
the glass are certified in either geometry. The scaling's cost and the extra copy's cost separately (only their net).
Input-to-photon.

**Falsifier.** `presentscale-preregistered` reddens if the method is weakened or the code drifts from it;
`presentscale-sealer` if a reading fires elsewhere than registered or a clamped geometry is accepted;
`presentscale-court` if a plant passes; `presentscale-fence` if a second variable enters the blit or the window, or
LATENCY-0's instrument is edited. On the host, a witness or client-area mismatch or a closed window yields no number,
and a reading that does not reproduce under `--confirm` is refuted.

## ORACLE-D0 — the oracle's third hash recomputed in place by Urðr's own code (the studio mints none of it)

**Why it is next.** Of `urdr-oracle-1`'s three hashes the kernel reproduces two natively, the frame digest and the
pixel sha. The third, `D_0`, is Urðr's composed CORE identity — level, entity, RNG stream and action log folded by
`statecanon` — and until now it was carried as evidence and checked by nothing here. GAME-0 carried Urðr's game layer
verbatim, with its suites running in place, and that layer holds every module `D_0` is composed from. So the third
hash can be checked without a second authority: by Urðr's own code, where it was frozen.

**The row.** `oracle-d0` runs a short driver in `oracle/game/` under GAME-0's environment. It imports Urðr's `gamegen`,
`entity`, `rngstream`, `actionlog` and `statecanon` and prints
`statecanon.d_n(gamegen.generate(seed, depth), entity.at(pos), rngstream.apply(rngstream.root(seed), []), actionlog.from_actions([]))`
for the oracle's own view: seed `0xABCDE`, depth 1, the entity at (34, 28), the RNG stream at its root and an empty
action log. The result must equal `urdr-oracle-1.json`'s `D_0` (`7d8d02e1…`). **Plant:** the same composition with the
entity one cell over must give a different `D_0`, so the row can go red.

**Grade.** ESTABLISHED (gate): the frozen `D_0` is reproduced by the tag's own code, in place, on every gate.
Verðandi writes none of the composition: no port, no twin, no re-derivation. The driver only calls `statecanon`.

**does_not_show.** That any other state composes as Urðr would: only the oracle's view with an empty log, plus the
one plant, is checked. That the kernel's picture depends on `D_0`, which it never reads, because VIEW does not read
CORE identity. Anything about movement or a non-empty action log. It is a check that the evidence the oracle carries
is consistent with the code carried beside it. It does not make the studio an authority over `D_0`.

**Falsifier.** `oracle-d0` goes red if the carried game layer, the oracle's `D_0` or the composition drifts, and the
plant goes red if `D_0` stops depending on the entity's position.

## PRESENT-STRETCH-0 — does the half-size blit's cost depend on GDI's stretch mode (a diagnostic; measured twice: `COLORONCOLOR` MODE MATERIAL reproduced, `HALFTONE` not reproduced)

**Why it is next.** PRESENT-SCALE-0, confirmed, found the 2:1 blit far dearer than the 1:1 blit on the owner's host,
under the device context's default stretch mode, 1 (`BLACKONWHITE`, a Boolean-AND reduction). That reading does not
say whether the cost belongs to the reduction as such or to that particular mode. This is the narrowest next question,
and it is a **diagnostic court**. It attributes. It adopts no mode, because each mode draws different pixels, so
choosing one for the shell changes what the window shows and would be its own court.

**The method (`f5372890`).** One variable at the half-size (960×540) destination: the stretch mode, one of
`BLACKONWHITE` (1, the default, now set explicitly), `COLORONCOLOR` (3, deletes the eliminated pixels) and `HALFTONE`
(4, averages them). Every present sets the mode and the brush origin (0, 0) before the blit, the same way in every
cell; only the mode's value differs. Everything else is FRAME-SPLIT-0's production path unchanged. The mode changes
between **blocks**, never between samples: 12 blocks, B C H H C B B C H H C B, each opening with 5 discarded warm-up
rounds. After each change the effective mode is read back from a device context and must equal the request, and the
client area is read back once and must be 960×540, or the court refuses. Per mode an envelope and a split are
recorded. The outcome is not predicted.

**The reading, on p50s, per mode against `BLACKONWHITE`.** **VOID** (the whole court) if any mode's |instrumentation
tax| ≥ 100‰ of its envelope. **CONFOUNDED** if that mode's six non-blit phases, summed, moved ≥ 50‰ of
`BLACKONWHITE`'s. Otherwise, if |blit(mode) − blit(`BLACKONWHITE`)| ≥ 100‰ of `BLACKONWHITE`'s blit, it reads **MODE
MATERIAL** (cheaper or dearer), and anything less reads **MODE IMMATERIAL**. p99s and the envelopes are reported
beside the reading and never folded into it.

**The instrument.** `shell/presentstretch.rs` is the court, generic over a `StretchSurface` (a `Surface` whose stretch
mode can be set and read back). On the host it runs over a stretch-mode GDI surface appended to `shell/win32.rs`,
after PRESENT-SCALE-0's section. Its present is LATENCY-0's `present_once` with `SetStretchBltMode` and
`SetBrushOrgEx` before the blit into the fixed half-size destination, in the plain overlapped window with LATENCY-0's
procedure. On the gate the court runs over the mock surface (`shell presentstretch-selftest`). The window build was
type-checked here; linking and running happen on the host. `verify/presentstretch.py` seals
`shell/attest/presentstretch-<host>.json`, and `--confirm` seals a separate confirmation record beside it.

**Rows.** `presentstretch-preregistered`: the method is locked, and the code's modes, block order, warm-up and
thresholds equal the registered ones. `presentstretch-sealer`: synthetic modes, where MODE MATERIAL (cheaper and
dearer, at exactly 100‰), MODE IMMATERIAL (99‰), CONFOUNDED (50‰) and a court-wide VOID fire at the registered
bounds, and a mode the device context did not honour, another client area or another block order is refused.
`presentstretch-court`: the court over the mock on the sealed session. Witnesses come first, the client area and each
block's effective mode are verified, all three modes are recorded, and each split sums to its total. Plants: a
tampered witness, an ignored mode and a mid-court close each refuse with no record. `presentstretch-fence`: only the
stretch mode changes, the timed interval holds no mode change and no hashing, and LATENCY-0's instrument is still a
byte-exact prefix.

**Measured (host DANIELDILLBERG, `shell/attest/presentstretch-DANIELDILLBERG.json`, cites PRESENT-STRETCH-0 `f5372890`).**
300 samples per cell over 12 blocks, no close. The client area read back as 960×540 and every block's effective mode
equalled its request (1, 3, 4). Measured refresh 13,379 µs. p50 / p99 in µs:

| | `BLACKONWHITE` (1, default) | `COLORONCOLOR` (3) | `HALFTONE` (4) |
|---|---|---|---|
| **blit** | **7,274 / 8,050** | **4,420 / 4,983** | **4,928 / 5,622** |
| blit − default, p50 | — | −2,854 (392‰) | −2,346 (322‰) |
| non-blit phases, p50 sum | 9,371 | 9,214 (−157, 16‰) | 9,230 (−141, 15‰) |
| instrumentation tax, p50 | −37 (2‰) | +44 (3‰) | −27 (1‰) |
| envelope render-start → frame-ready | 16,722 / 19,067 | 13,676 / 15,797 | 14,201 / 16,244 |
| frame-ready → composited | 8,873 / 12,402 | 11,436 / 14,891 | 11,018 / 14,331 |

**The reading: `COLORONCOLOR`: MODE MATERIAL (cheaper); `HALFTONE`: MODE MATERIAL (cheaper).** Each non-default
mode's blit p50 fell far past the 100‰ bound below `BLACKONWHITE`'s (392‰ and 322‰). The non-blit phases moved 16‰ and
15‰, well inside the 50‰ confound bound, and every tax was 3‰ or less. So on this host, in this exact GDI apparatus
and workload, the half-size blit's cost depended materially on the stretch mode, and the default `BLACKONWHITE` was
the dearest of the three modes measured. That is not a statement about GDI's stretch modes in general. The rule
compares each mode only with the default. That `COLORONCOLOR` read 508 µs cheaper than `HALFTONE` at p50 is beside
the rule and is not ruled on.

**Beside the reading, not ruled on.** frame-ready → composited p50 rose by 2,563 µs (`COLORONCOLOR`) and 2,145 µs
(`HALFTONE`), most of each blit saving. In this loop a frame that finishes earlier waits longer for the composition:
the locked-phase absorption LATENCY-1R measured (`GHOSTS.md` G7). Every mode's envelope p50 stayed above the measured
refresh. The blit result is therefore not an end-to-end latency result. The default's blit here (7.27 ms, the mode
now set explicitly before every present) is a little below PRESENT-SCALE-0's half-size readings (7.46–7.76 ms). That
is a cross-court difference, recorded and not interpreted. The three modes draw different pixels: `BLACKONWHITE` ANDs
the eliminated pixels, `COLORONCOLOR` deletes them and `HALFTONE` averages them. Those semantics come from GDI's
documentation and are not verified on the glass. What the shell should show remains a separate court.

**Confirmation (`shell/attest/presentstretch-confirm-DANIELDILLBERG.json`, cites the first record).** The same
blocks and modes, every effective mode equal to its request, the client area 960×540. Measured refresh 13,563 µs.
p50 / p99 in µs:

| | `BLACKONWHITE` (1, default) | `COLORONCOLOR` (3) | `HALFTONE` (4) |
|---|---|---|---|
| **blit** | **11,589 / 12,416** | **6,382 / 7,181** | **7,202 / 9,037** |
| blit − default, p50 | — | −5,207 (449‰) | −4,387 (378‰) |
| non-blit phases, p50 sum | 11,339 | 10,784 (−555, **48‰**) | 10,730 (−609, **53‰**) |
| instrumentation tax, p50 | −89 (3‰) | −30 (1‰) | +136 (7‰) |
| envelope render-start → frame-ready | 22,817 / 25,153 | 17,386 / 19,400 | 17,982 / 20,301 |
| frame-ready → composited | 3,748 / 14,080 | 9,096 / 12,403 | 8,437 / 12,113 |

This run reads **`COLORONCOLOR`: MODE MATERIAL (cheaper); `HALFTONE`: CONFOUNDED.** Two statements follow from it,
and both stand as written:

- **Per mode, as the rule is registered** (each mode read separately against the default), `COLORONCOLOR`'s reading
  reproduced: MODE MATERIAL (cheaper) in both runs, at 392‰ and then 449‰ of the default's blit. `HALFTONE`'s did
  not. It read MODE MATERIAL, then CONFOUNDED: its non-blit phases moved 53‰ against the 50‰ bound while its blit was
  still 378‰ cheaper. Under the registered failure condition, the first run's `HALFTONE` reading is not carried
  forward, because it did not reproduce. The question itself is unresolved rather than answered the other way:
  CONFOUNDED declines to attribute, and it does not read IMMATERIAL.
- **The court's combined label** did not reproduce, and the confirmation record says so: its sealer compares the
  whole label, both modes together. The sealer is not changed after the number.

**Beside the confirmation, not ruled on.** The whole second run was much slower than the first at a similar refresh.
The default's blit p50 went from 7,274 to 11,589 µs (+59%), its non-blit phases from 9,371 to 11,339 µs (+21%) and
its envelope from 16.7 to 22.8 ms. The cause is not measured here. The within-run comparison reproduced for
`COLORONCOLOR`, but the absolute saving did not reproduce as a number (2.85 ms, then 5.21 ms), so no millisecond
figure is carried as confirmed. In this run the non-blit phases also moved more with the mode (48‰ and 53‰, against
16‰ and 15‰ before), spread over frame, emit and bgr. `COLORONCOLOR` passed the confound bound with 2‰ to spare
(`GHOSTS.md` G10). frame-ready → composited related differently to the refresh this time: under the default its p50
was 3,748 µs (8,873 before), with its p95 at 11,444 µs. That is recorded and not interpreted.

**Grade.** DECLARED: the method (hash-locked). ESTABLISHED (gate): the court's logic, the mode and client-area
refusals and the sealer's rule. MEASURED (host, two runs), on this host and apparatus:
- `COLORONCOLOR`'s blit was materially cheaper than `BLACKONWHITE`'s: MODE MATERIAL in both runs (392‰ and 449‰ at
  p50). This reproduced per mode, with the confound bound passed at 16‰ and 48‰. The size of the saving in
  milliseconds did not reproduce.
- `HALFTONE`: MODE MATERIAL, then CONFOUNDED. It did not reproduce, so the first reading is not carried forward, and
  the question is unresolved.
- The court's combined label did not reproduce.

No mode is adopted, and the shell still blits under the device context's default.

**does_not_show.** Which stretch mode the shell should use, or whether it should use one at all. That the modes'
pixel semantics are what GDI documents them to be: they are recorded from the documentation and not verified on the
glass. Anything about a destination other than 960×540, or a present path other than `StretchDIBits` into a GDI
window. Input-to-photon.

**Falsifier.** `presentstretch-preregistered` goes red if the method is weakened or the code drifts from it.
`presentstretch-sealer` goes red if a reading fires anywhere other than where it was registered, or if an unhonoured
mode is accepted. `presentstretch-court` goes red if a plant passes, and `presentstretch-fence` if a second variable
enters the present or the timed interval. On the host, a witness, mode or client-area mismatch, or a closed window,
yields no number, and a reading that does not reproduce under `--confirm` is refuted.

## ALLOC-REUSE-0 — how much of the frame is allocating its buffers every frame (a diagnostic; measured and confirmed: ALLOCATION MATERIAL, reuse cheaper)

**Why it is next.** FRAME-SPLIT-0 attributes each buffer's allocation to the phase it happens in: the strips vector
to strips, the 2 MB index frame to frame, the 6 MB pixel buffer to emit and the 6 MB BGR buffer to bgr (`GHOSTS.md`
G8). The split cannot say how much of those phases is the allocation itself. This court asks that, as a
**diagnostic**. It attributes. It adopts nothing: reusing buffers in the production path would be its own change and
its own court.

**The method (`aaaada37`).** One variable, the buffers' lifetime. **Fresh** is the production path, where the buffers
are allocated every frame (`arm_composite` / `arm_composite_marked` + `to_blit`). **Reused** allocates them once and
overwrites them every frame (`arm_composite_reuse_marked` + `to_blit_into`). The same calls run in the same order with
the same five marks. The floor swizzle's buffer belongs to `fast::blocked_floor` and stays fresh in both variants,
because `fast.rs` is untouched. Everything else is FRAME-SPLIT-0's apparatus unchanged: the production half-size
window and default stretch mode, the sealed session, the GDI present and the locked phase origin. Witnesses come
first. The reused buffers' index frame, composite and blit bytes must equal the fresh path's for every sealed frame
before any clock runs, and every composite and blit buffer is checked again after its sample. Then come four cells
(fresh envelope, fresh split, reused envelope, reused split), interleaved ABBA after 10 warm-up rounds. The outcome is
not predicted.

**The reading, on p50s.** **VOID** if either variant's |instrumentation tax| ≥ 100‰ of its envelope. **CONFOUNDED** if
the phases whose allocation does not change (floor swizzle, HUD and blit, summed) moved ≥ 50‰ of the fresh sum.
Otherwise, with dE = envelope(reused) − envelope(fresh), |dE| ≥ 50‰ of the fresh envelope reads **ALLOCATION
MATERIAL** (reuse cheaper or dearer), and anything less reads **ALLOCATION IMMATERIAL**. The per-phase deltas (strips,
frame, emit, bgr) are reported beside the reading, to show where any cost sits, and are never ruled on.

**The instrument.** `shell/allocreuse.rs` is the court, over LATENCY-1R's `Surface`. `shell/present.rs` gains the
reuse path, which is the marked mirror's calls in the persistent `ReuseBufs`, plus `to_blit_into`, which is
`to_blit`'s transform into a given buffer. On the host the court runs in FRAME-SPLIT-0's window over LATENCY-1R's GDI
surface, through a driver appended to `shell/win32.rs`. On the gate it runs over the mock surface
(`shell allocreuse-selftest`). `verify/allocreuse.py` seals `shell/attest/allocreuse-<host>.json`, and `--confirm`
seals a separate confirmation record beside it.

**Rows.** `allocreuse-preregistered`: the method is locked, and the code's warm-up, phase groups and thresholds equal
the registered ones. `allocreuse-sealer`: synthetic variants, where ALLOCATION MATERIAL (reuse cheaper and dearer, at
exactly 50‰ of the fresh envelope), IMMATERIAL (49‰), CONFOUNDED (50‰) and VOID fire at the registered bounds. The
per-phase deltas are recorded as measured, and another warm-up or phase order is refused. `allocreuse-court`: the
court over the mock on the sealed session, with witnesses first (including the reused bytes' equality), four cells
after the warm-up, and each split summing to its total. Plants: a tampered witness and a mid-court close each refuse
with no record. `allocreuse-fence`: the reuse path makes the marked mirror's calls in its order with the same five
marks and allocates none of its buffers (only `fast::blocked_floor` still allocates, in both variants), `to_blit_into` is
`to_blit`'s transform, the court runs in FRAME-SPLIT-0's window and
checks both variants' bytes after every sample, and LATENCY-0's instrument is still a byte-exact prefix.

**Measured (host DANIELDILLBERG, `shell/attest/allocreuse-DANIELDILLBERG.json`, cites ALLOC-REUSE-0 `aaaada37`).**
300 samples per cell after 10 warm-up rounds, no close. The reused buffers' bytes equalled the fresh path's on every
sealed frame before the clock and after every sample. Measured refresh 13,773 µs. p50 / p99 in µs:

| | fresh (production) | reused | reused − fresh, p50 |
|---|---|---|---|
| **envelope render-start → frame-ready** | **17,294 / 19,380** | **15,705 / 17,671** | **−1,589 (91‰)** |
| strips | 63 / 167 | 56 / 109 | −7 |
| frame (the 2 MB index frame) | 3,741 / 5,204 | 3,678 / 5,047 | −63 |
| emit (the 6 MB pixel buffer) | 3,782 / 4,944 | 3,110 / 4,177 | −672 |
| bgr (the 6 MB BGR buffer) | 1,869 / 2,517 | 1,023 / 1,752 | −846 |
| unchanged phases (floor swizzle, HUD, blit), p50 sum | 7,988 | 7,905 | −83 (10‰) |
| instrumentation tax, p50 | −225 (13‰) | +56 (3‰) | |
| frame-ready → composited | 8,290 / 12,411 | 9,639 / 13,366 | +1,349 |

**The reading: ALLOCATION MATERIAL (reuse cheaper).** The envelope p50 fell 1,589 µs, 91‰ of the fresh envelope and
past the 50‰ bound. The phases whose allocation does not change moved 10‰, inside the 50‰ confound bound, and both
taxes stayed far inside the VOID bound. So on this host, in this apparatus and workload, allocating the strips,
index-frame, pixel and BGR buffers every frame was a material part of the frame: about 1.6 ms of a ~17.3 ms envelope
at the median. Nothing is adopted, and the production path still allocates fresh buffers every frame.

**Beside the reading, not ruled on.** The per-phase deltas show where the saving sat: bgr (−846 µs) and emit
(−672 µs), the phases of the two 6 MB buffers, carry 96% of the allocating phases' combined change, while frame
(−63 µs, the 2 MB index frame) and strips (−7 µs) carry almost none. They are reported, never ruled on, and why the
index frame moved so little is not measured here. frame-ready → composited p50 rose 1,349 µs, again the locked-phase
absorption (`GHOSTS.md` G7). Both envelopes stayed above the refresh, so this is not an end-to-end latency result.
The fresh envelope here (17.3 ms) reads above FRAME-SPLIT-0's 15.7 ms in the same window on the same arm, as
PRESENT-SCALE-0's half-size condition did (17.0–17.1 ms). That is a cross-court difference, recorded and not
interpreted.

**Confirmed (`shell/attest/allocreuse-confirm-DANIELDILLBERG.json`, cites the first record).** The preregistered
second run reads **ALLOCATION MATERIAL (reuse cheaper)** again, and the confirmation record states that the reading
reproduced. The reused bytes again equalled the fresh path's throughout. Measured refresh 13,157 µs. p50 / p99 in µs:

| | fresh (production) | reused | reused − fresh, p50 |
|---|---|---|---|
| **envelope render-start → frame-ready** | **17,358 / 19,360** | **15,534 / 17,724** | **−1,824 (105‰)** |
| strips | 69 / 217 | 56 / 131 | −13 |
| frame (the 2 MB index frame) | 3,672 / 5,075 | 3,404 / 4,942 | −268 |
| emit (the 6 MB pixel buffer) | 3,843 / 4,908 | 3,116 / 4,150 | −727 |
| bgr (the 6 MB BGR buffer) | 1,922 / 2,814 | 1,024 / 1,664 | −898 |
| unchanged phases (floor swizzle, HUD, blit), p50 sum | 8,037 | 8,060 | +23 (2‰) |
| instrumentation tax, p50 | +92 (5‰) | −99 (6‰) | |
| frame-ready → composited | 8,301 / 11,787 | 9,794 / 13,575 | +1,493 |

The envelope saving was 105‰ of the fresh envelope (91‰ in the first run). The unchanged phases moved 2‰ (10‰ before),
further from the confound bound. The fresh envelope was steady across the two runs (17,294 and 17,358 µs). bgr and
emit again carried most of the change (−898 and −727 µs, against −846 and −672), and frame moved more this time
(−268 µs, against −63). The per-phase numbers stay beside the rule. frame-ready → composited p50 rose again
(+1,493 µs), so this is still not an end-to-end latency result.

**Grade.** DECLARED: the method (hash-locked). ESTABLISHED (gate): the reuse path is byte-equal to the fresh path on
every sealed frame, and the court's logic and the sealer's rule hold. MEASURED (host, two runs): ALLOCATION MATERIAL,
reuse cheaper by 1.59 and 1.82 ms (91‰ and 105‰) at the envelope p50. The reading reproduced on this host and
apparatus, with the reused bytes equal to the fresh path's throughout. Nothing is adopted: the production path still
allocates its buffers every frame, and adopting reuse would be its own court.

**does_not_show.** That the production path should reuse its buffers. Anything about another allocator, OS or buffer
size: a fresh buffer's cost includes whatever this host's allocator and OS do for it (zeroing, first-touch page
faults). The floor swizzle's allocation, which stays fresh in both variants. A per-phase verdict. Input-to-photon.

**Falsifier.** `allocreuse-preregistered` goes red if the method is weakened or the code drifts from it.
`allocreuse-sealer` goes red if a reading fires anywhere other than where it was registered. `allocreuse-court` goes
red if a plant passes, and `allocreuse-fence` if the reuse path changes a call, a mark or a byte, or starts to
allocate a buffer. On the host, a witness or reuse-byte mismatch, or a closed window, yields no number, and a reading that does
not reproduce under `--confirm` is refuted.

## ALLOC-REUSE-1 — does the persistent-buffer render-loop entry earn adoption (an adoption court; measured twice: PERFORMANCE PASS in both runs, ADOPT)

**Why it is next, and what it can adopt.** ALLOC-REUSE-0, confirmed, attributed 91‰ and then 105‰ of the envelope to
allocating the frame's buffers every frame. Reading the code before preregistering turned up a boundary: **the
shipped shell has no per-frame render loop.** `run` renders once. `playback-window` pre-renders every frame and every
blit before its window opens, so each stored frame has to own its buffers. The per-frame allocation that ALLOC-REUSE-0
measured happens only in the courts' modelled render loop (`GHOSTS.md` G12), which is the loop a future live window
will need. So this court can adopt an **entry contract**, not a change to a shipped window:
`present::LoopRenderer` as the production entry for any loop that renders once per presented frame. The fresh path
(`compose_frame`, `arm_composite`, `fast::render`, `to_blit`) stays the **frozen reference and differential oracle**,
and it is never deleted or rewritten. ALLOC-REUSE-0's numbers are the motivation, not the adoption evidence.

**The candidate.** `LoopRenderer` makes `fast::render`'s calls in `fast::render`'s order (the strips, the index frame,
the floor swizzle, the threaded pixel pass at `PROD_THREADS`) and then the HUD, into four buffers it allocates once in
`new()` and overwrites on every render. Its `blit()` is `to_blit`'s transform into its own BGR buffer. Only the floor
swizzle's small buffer, which belongs to `fast::blocked_floor` (fast.rs is untouched), is still allocated per render.

**Correctness first, on every gate.** One `LoopRenderer`, its byte buffers first
filled with a poison byte, renders 23 cases: every corpus scene × tile set (12, with the goldens), the adversarial
witness cameras (7 more) and the sealed session's 4 frames. It renders them in three orders (forward, reverse, zigzag),
so every render starts from another scene's leftovers. Each of the 69 renders must equal the fresh reference byte for
byte (index frame, viewport, composite and blit). The corpus's frame digests and pixel shas must equal the goldens, the
session's frame digests must equal their sealed witnesses, and no buffer may ever be replaced: each buffer's address
and capacity are checked after every render.

**Then performance, on the host (`dc904a6c`).** Witnesses first: the fresh path reproduces every sealed frame witness,
and the poisoned loop renderer reproduces the fresh index frame, composite and blit. Then the uninstrumented envelope
render-start → frame-ready is measured for fresh and reused, **interleaved ABBA in the same run**, after 10 warm-up
rounds, with **1000 samples per cell**. Every composite and blit is compared after its composition, and the buffers are
checked persistent after every sample. The rule:

    PERFORMANCE PASS  iff  p99(reused) ≤ 950‰ × p99(fresh), in the same run

The 50‰ is an **adoption margin**: a declared engineering decision threshold, not a measurement uncertainty or a
confidence interval. **ADOPT** requires PERFORMANCE PASS in the run **and** in its `--confirm` run. Anything else is
**REJECT**. The comparator is the fresh path in the same run, because a p99 sealed in another run would bring in
cross-run drift like PRESENT-STRETCH-0's +59% (`GHOSTS.md` G10). N = 1000 makes p99 the 11th-largest sample rather than
the 3rd, and the 12 largest samples per variant are recorded beside it. (The locked entry calls it the 10th-largest.
Under the nearest-rank percentile the courts use, ten samples lie beyond it, so it is the 11th. The entry stays as
locked. The rule used the p99 as the court computes it, so the reading is unaffected.) The p50s and frame-ready → composited are
recorded beside the rule and never decide. On ADOPT, a following patch declares `LoopRenderer` the sole production
entry for in-loop rendering, with a call-site fence that a new live loop cannot bypass. On REJECT, it stays an unused
candidate and ALLOC-REUSE-0's diagnostic stands.

**The instrument.** `shell/allocreuse1.rs` holds both courts: `loop_equiv` (the gate's correctness court, no clock,
`shell loop-equiv`) and `court` (the performance court, over LATENCY-1R's `Surface`). On the host the performance court
runs in FRAME-SPLIT-0's window over LATENCY-1R's GDI surface, through a driver appended to `shell/win32.rs`. On the gate
it runs over the mock (`shell allocreuse1-selftest`). `verify/allocreuse1.py` seals
`shell/attest/allocreuse1-<host>.json`. Its `--confirm` run seals `allocreuse1-confirm-<host>.json` and states ADOPT or
REJECT in its reading; the verdict is never stored as a data key. Each record carries HOST-STATE-0's before and after
snapshots, attached after the label is fixed.

**Rows.** `allocreuse1-preregistered`: the method is locked, and the code's per-cell count, warm-up, tail and margin
equal the registered ones. `allocreuse1-equiv`: the correctness court above. Plants: a renderer that skips the pixel
pass on alternate renders is caught (LOOP-EQUIV), and a replaced buffer is caught (LOOP-PERSIST). `allocreuse1-sealer`:
synthetic runs read PERFORMANCE PASS exactly at 950‰ and FAIL one microsecond above. The p50s never move the label,
and ADOPT follows only PASS then PASS. A run that is not 1000 per cell, not ABBA, not warmed up, or has an unrendered
sample or a malformed tail is refused. `allocreuse1-court`: the court over the mock on the sealed session. It reads
PERFORMANCE FAIL under the mock, whose equal ticks give 1000‰. Plants: a tampered witness, a mid-court close and a
replaced buffer each refuse with no record. `allocreuse1-fence`: the loop renderer makes `fast::render`'s calls in
order and allocates only in `new()`, and its render is exactly viewport then overlay. The fresh reference's source is
pinned by hash. No file except `present.rs` and `allocreuse1.rs` names `LoopRenderer`, so no shipped window uses it.
The court runs in FRAME-SPLIT-0's window with the locked phase origin and nothing but rendering and the blit inside its
interval. LATENCY-0's instrument is still a byte-exact prefix.

**Measured (host DANIELDILLBERG, `shell/attest/allocreuse1-DANIELDILLBERG.json`, cites ALLOC-REUSE-1 `dc904a6c` and
HOST-STATE-0 `58250382`).** 1000 samples per cell after 10 warm-up rounds, no close. The witnesses reproduced, every
sample's composite and blit equalled their verified bytes, and the loop's buffers stayed persistent through all 1,014
loop renders. Measured refresh 13,356 µs. In µs:

| | fresh (reference) | reused (`LoopRenderer`) | reused against fresh |
|---|---|---|---|
| **envelope p99 (the rule)** | **17,604** | **15,600** | **886‰ (−2,004)** |
| envelope p50 / p95 | 15,469 / 16,812 | 13,703 / 14,926 | −1,766 at p50 |
| envelope max | 20,994 | 21,538 | |
| frame-ready → composited p50 / p99 | 10,264 / 12,745 | 12,006 / 14,464 | +1,742 at p50 |

**PERFORMANCE PASS**: reuse's p99 was 886‰ of fresh's, inside the 950‰ adoption bound.

**Confirmed (`shell/attest/allocreuse1-confirm-DANIELDILLBERG.json`, cites the first record).** The same apparatus,
about 45 minutes later. Measured refresh 13,240 µs. In µs:

| | fresh (reference) | reused (`LoopRenderer`) | reused against fresh |
|---|---|---|---|
| **envelope p99 (the rule)** | **25,598** | **23,797** | **929‰ (−1,801)** |
| envelope p50 / p95 | 21,808 / 24,433 | 20,058 / 22,688 | −1,750 at p50 |
| envelope max | 30,527 | 26,256 | |
| frame-ready → composited p50 / p99 | 4,830 / 12,311 | 6,521 / 13,266 | +1,691 at p50 |

**PERFORMANCE PASS** again (929‰), so the confirmation record reads **ADOPT**: both preregistered runs passed, with
correctness holding on every sample of both.

**Beside the rule, not ruled on.** The second run was much slower as a whole: fresh's envelope p50 went from 15,469
to 21,808 µs (+41%) at a similar refresh. The margin under the bound shrank with it, from 64‰ to 21‰. The saving in
microseconds held steady: p99 −2,004 and then −1,801 µs, and p50 −1,766 and then −1,750 µs. In both runs the reused
cell's frame-ready → composited p50 rose by about as much as its envelope fell (+1,742 and +1,691 µs). The frame is
ready earlier and waits longer for the composition, the locked-phase absorption of `GHOSTS.md` G7, so this is not an
end-to-end latency result. The tails: the 12 largest render samples per variant are in each record. In the first run
one reused sample (21,538 µs) was the largest of either cell, and reuse's second-largest was 18,208 µs. The fresh
envelope p50 here (15.5 ms, then 21.8 ms) against ALLOC-REUSE-0's 17.3 ms in the same window is a cross-court and
cross-run difference, recorded and not interpreted.

**Host state beside each run (HOST-STATE-0, association only).** Before both runs the OS reported the same CPU clock
state (per-processor current MHz 1,610 median, 2,000 max), the Balanced plan, AC power and a 75 Hz mode. The recorded
difference was memory: before the slower second run the memory load was 96% with 359 MB available, against 89% with
1,222 MB before the first. The CPU was less busy before the slower run (24‰ against 72‰). After each run the memory
load read 88–89%. This is a coincidence the record now carries, not a cause (`GHOSTS.md` G13).

**Grade.** DECLARED: the method (hash-locked). ESTABLISHED (gate): the loop renderer is byte-identical to the fresh
path over the corpus, the adversarial cameras and the sealed session, in three orders from poisoned buffers, with its
buffers persistent; the court's logic and the sealer's rule hold. MEASURED (host, two runs): PERFORMANCE PASS both
times, with reuse's envelope p99 at 886‰ and then 929‰ of fresh's in the same run. So the preregistered reading is
**ADOPT**, on this host and apparatus. What ADOPT does is declared by the following patch (ALLOC-REUSE-1 LOCK). No
shipped window changes, because none renders per frame (`GHOSTS.md` G12).

**does_not_show.** That any shipped window is faster: none renders through the entry. That the entry's saving holds
under another allocator, OS, host or buffer size. The floor swizzle's allocation, which stays per render. What a live
loop's timing, cadence, input or ownership should be: that is the live-loop rung's own court. Input-to-photon.

**Falsifier.** `allocreuse1-equiv` goes red on one differing byte, one missed golden or one replaced buffer.
`allocreuse1-fence` goes red if the renderer allocates, reorders a call, or is named by a shipped file, or if the fresh
reference is edited. `allocreuse1-sealer` goes red if the label moves at the margin, if a p50 decides, or if one
passing run adopts. On the host, a witness, drift or persistence failure, or a closed window, yields no number, and
REJECT follows unless both runs pass.

## HOST-STATE-0 — the host's state recorded beside a court, never controlled (an apparatus; landed)

**Why.** PRESENT-STRETCH-0's confirmation ran with the default mode's blit p50 59% higher than its first run
(7,274 → 11,589 µs) at a similar refresh, and no court could say why. HOST-STATE-0 records what the OS reports about
the host, so the next drift can be set beside a host-state change. A drift that coincides with no recorded change is
also evidence: it says the recorded state is insufficient. **Record, don't control.** It changes nothing on the host,
and it is not a prerequisite for any court.

**The method (`58250382`).** `verify/hoststate.py` takes a snapshot of eight registered fields, in order. `cpu`: the
model, logical processors, and per-processor MHz as `CallNtPowerInformation` reports them. `power`: AC line and
battery state, battery saver, and the active plan (`powercfg /getactivescheme`, a query). `load`: the system's CPU busy
share over a 1000 ms window. `memory`: memory load and physical memory. `process`: the sealing process's priority class
and affinity. `display`: the screen's logical and physical size, depth and nominal refresh. `uptime`. `thermal`:
declared not captured, because there is no reliable source without elevation. Each field is captured on its own, and
one that fails is recorded as unavailable with its reason. Every value is an integer or a string. Off Windows every
field is unavailable. `capture_safe` never raises. A court opts in through `diagcommon.host_run(probe=…)`, which takes
one snapshot just before its window court and one just after. ALLOC-REUSE-1 is the first court to opt in. The
diagnostic courts' flow is unchanged. `python verify/hoststate.py` prints one snapshot and writes nothing.

**Rows.** `hoststate-preregistered`: the method is locked, and the fields and load window equal the registered ones.
`hoststate-record`: on this gate every field is unavailable with the registered marker. The Windows capture path, run
where its APIs are absent, degrades field by field. A planted failure, a float, a boolean or a missing field becomes
an unavailable snapshot, never an exception, and a Windows-shaped snapshot validates. The source calls no control API,
writes no file and runs one command, the query. `hoststate-fence`: one ALLOC-REUSE-1 raw sealed with no probe and with
two different host states gives the same label, derived numbers and reading. The rule takes only the derived variants,
and the host state is attached after the label and the adoption are fixed. The probe is optional and taken through
`capture_safe`, and the diagnostic sealers pass none.

**First host snapshots (DANIELDILLBERG).** A standalone look (`python verify/hoststate.py`) and ALLOC-REUSE-1's two
runs each captured every field on the host, with no field unavailable except thermal, as declared. The host reads as
an AMD Ryzen AI Z2 Extreme, 16 logical processors, 11,897 MB of memory, on AC power under the Balanced plan, with a
1920×1080 32-bit mode at a nominal 75 Hz. The reported per-processor MHz never exceeded 2,000, including the limit.
That is consistent with the recorded interpretation limit that `CallNtPowerInformation` need not show boost or the
effective clock, so the CPU field cannot say whether the clock differed between runs. The runs' before and after
snapshots are set out under ALLOC-REUSE-1 above. What they put beside the second run's slowdown is memory pressure (96%
load, 359 MB available before it). That is an association, not a cause (`GHOSTS.md` G13).

**Grade.** DECLARED: the method. ESTABLISHED (gate): the recorder's shape, its degradation, its independence from
every rule, and its non-blocking use. MEASURED (host): every Windows field but thermal, as the OS reports it, in one
standalone snapshot and in four snapshots around two court runs.

**does_not_show.** That a recorded state caused, explains or corrects any number: association, never cause. That the
OS-reported MHz is the effective clock. The court process's own priority (only the sealing process's). Thermal state.

## ALLOC-REUSE-1 LOCK — the persistent-buffer render-loop entry adopted (seat 24)

**What is adopted.** ALLOC-REUSE-1 read PERFORMANCE PASS on its run and on its confirmation (886‰ and 929‰), so its
preregistered reading is ADOPT. This rung carries out what the entry said ADOPT would do. `present::LoopRenderer` is
now **the production entry for in-loop rendering**: a loop that renders once per presented frame renders through it.
Its declaration says so in the source. The fresh path (`compose_frame`, `arm_composite`, `fast::render`, `to_blit`)
stays the frozen reference and differential oracle, its source pinned (`allocreuse1-fence`) and never rewritten.

**What is not changed.** No shipped window. `run` still renders once, and `playback-window` still pre-renders frames
that own their buffers (`GHOSTS.md` G12). The adoption is the contract a future live loop enters, not a speed-up of
anything that ships today. The courts that measure against the fresh path keep measuring against it.

**The call-site fence (row `allocreuse1-lock`).** Every call site of a fresh render entry in the shell (`compose_frame`,
`arm_composite`, the marked mirrors, `fast::render`, the emits, `to_blit`) is pinned by count, per file: present.rs's
definitions, `run`'s single compose, playback's owned pre-render, the court modules and LATENCY-0's prefix. A new site
reddens the gate. Either it is a loop rendering around the adopted entry, or it is a new reference site and is
re-pinned on purpose, in the patch that adds it. The row also requires the renderer to declare its adoption. Where the
checkout carries the two host records (the owner's does), the row checks that they are the pinned ones
(`8036e654`, `256e8a6e`), that both read PERFORMANCE PASS, that the confirmation cites the first, and that it reads
ADOPT. `allocreuse1-fence` no longer forbids other files from naming the renderer, because since the ADOPT a live loop
should.

**Grade.** ESTABLISHED (gate): the entry is byte-identical to the fresh reference (`allocreuse1-equiv`), declared
adopted, and the only sanctioned way for new code to render per frame (`allocreuse1-lock`). MEASURED (host, two runs,
ALLOC-REUSE-1): its envelope p99 at 886‰ and 929‰ of the fresh path's in the same run.

**does_not_show.** That any shipped window got faster. That the saving holds on another host, allocator, OS or buffer
size, or reaches the glass: in this loop the frame waited longer at the composition by about what it saved (`GHOSTS.md`
G7). What the live loop's cadence, ownership and input should be: that is its own rung, which renders through this
entry.

**Falsifier.** `allocreuse1-lock` goes red on any new fresh-render call site in the shell, on a renderer that stops
declaring its adoption, or on host records that are not the pinned ADOPT pair. `allocreuse1-equiv` and
`allocreuse1-fence` go on guarding the entry's bytes, its allocation and the frozen reference.

## PRESENTATION-CHOICE-0 — what the shell shows: the certified picture, 1:1, in a borderless window (a decision; declared)

**The decision (`4a7a32d9`).** PRESENT-SCALE-0 and PRESENT-STRETCH-0 measured what the half-size window costs and
deliberately chose nothing, because each option changes what the window shows. The owner has now chosen. The shell
shows **the certified picture, 1:1**: the kernel's 1920×1080 composite, pixel for pixel, with no reduction by GDI or by
the kernel. It shows it in a **borderless window covering the 1920×1080 screen at (0,0)**, so the whole frame is
visible. No new VIEW law is needed, because the picture on the screen is meant to be the picture the gate certifies.
The options considered and not chosen were a certified 2:1 reduction (new VIEW semantics) and a stated GDI stretch mode
(pixels nothing checks).

**What conforms.** An implementation presents the certified composite with destination = source = 1920×1080 and no
scaling at any layer the shell controls. That means no GDI stretch and no DPI virtualisation: the process is DPI-aware
and the screen's logical and physical size are both 1920×1080. The window is a borderless popup whose 1920×1080 client
sits at the screen's (0,0). And a witness shows it: the composed screen under the window, read back, equals the
certified picture byte for byte. Which call implements it is PRESENT-EXACT-0's court.

**Row.** `presentationchoice-declared`: the decision is registered with its conformance clauses and its hash intact.

**Grade.** DECLARED: a semantic decision, hash-locked. It earns nothing until an implementation is witnessed against
it.

**does_not_show.** That the half-size windows conform: `run` and `playback-window` (LATENCY-0's frozen instrument) do
not, and they are not changed. The conforming presenter, `shell show`, is locked by PRESENT-EXACT-0 LOCK (below). Also out of
scope: anything after composition (scan-out, the panel, display-side colour processing), and another screen size or
scaling setting.

## PRESENT-EXACT-0 — which GDI call presents the certified picture 1:1, with the composed screen read back (measured twice: the screen read back exact; NO MATERIAL DIFFERENCE; SetDIBitsToDevice adopted)

**Why it is next.** PRESENTATION-CHOICE-0 fixed the target. This court picks the call that implements it, and adds
the witness G11 said was missing: something that checks what reaches the screen, not only the bytes handed to GDI.

**The method (`bc910e2f`).** A borderless, topmost 1920×1080 popup at the screen's (0,0), the process made DPI-aware
first. ONE variable, the present call: **StretchDIBits at 1:1** (destination = source) or **SetDIBitsToDevice** (no
stretch path at all). Both presents otherwise keep LATENCY-0's `present_once` shape (GetDC, the call, frame-ready,
DwmFlush, composited, ReleaseDC), and no stretch mode is touched. Frames render through the adopted `LoopRenderer`.

**The witness, a hard gate.** Before any clock, the geometry is verified: a client of 1920×1080 at screen (0,0), on a
screen whose logical and physical size are both 1920×1080. Then, for every sealed frame and each call: the window is
cleared to white through `PatBlt`, a path that is neither call, and the white is read back. The call presents the
frame. The **composed screen** under the window is read back (a screen-DC `BitBlt` into a 24-bit top-down DIB) and
must equal the certified blit bytes, with zero differing bytes. Clearing first means a call that wrote nothing cannot
pass on the previous call's pixels. After the court, the last frame is read back again under each call. Any mismatch,
stale readback or wrong geometry refuses the court, with no record.

**The reading, on the same-run p99 of the envelope** render-start → frame-ready (render, blit and call), the two
calls interleaved ABBA after 10 warm-up rounds, 1000 samples per cell. **STRETCHDIBITS CHEAPER** if its p99 is at most
950‰ of SetDIBitsToDevice's. **SETDIBITSTODEVICE CHEAPER** if the reverse holds. **NO MATERIAL DIFFERENCE** otherwise.
The 50‰ is an adoption margin, a declared decision threshold. **The adoption**, read by `--confirm`: StretchDIBits only
if both runs read it cheaper; otherwise **SetDIBitsToDevice**, the simpler semantics. The p50s, the call interval (call
start → frame-ready) and frame-ready → composited are reported beside the rule and never decide. HOST-STATE-0's
snapshots are recorded beside each run.

**The instrument.** `shell/presentexact.rs` is the court, over an `ExactSurface`: a `Surface` that can set its call,
clear, read the screen back and report its geometry. On the host it runs over a borderless GDI surface appended to
`shell/win32.rs`. On the gate it runs over a mock screen that holds what was last presented. `verify/presentexact.py`
seals `shell/attest/presentexact-<host>.json`, and its `--confirm` record states the adopted call in its reading. The
window build was type-checked here; linking and running happen on the host.

**Rows.** `presentexact-preregistered`: the method is locked, and the code's calls, per-cell count, warm-up, tail,
margin and target equal the registered ones. `presentexact-sealer`: synthetic runs read each call cheaper exactly at
950‰ and NO MATERIAL DIFFERENCE one microsecond short, and the p50s never move the label. StretchDIBits is adopted only
for cheaper-then-cheaper, and SetDIBitsToDevice in the other eight cases. One differing readback byte, a short
readback, a client below a title bar, a scaled screen, 300 samples per cell, another render entry or another block
order is refused. `presentexact-court`: the court over the mock, with 10 readback checks, reading NO MATERIAL
DIFFERENCE under the mock. Plants: a tampered witness, a mid-court close, a client below a title bar, one byte changed
on the way back, and a call that writes nothing each refuse with no record. `presentexact-fence`: only the call
changes, and no stretch mode is touched. The window is a DPI-aware, borderless, topmost 1920×1080 popup at (0,0). The
clear is a white `PatBlt` and the readback a screen-DC `BitBlt`. The timed interval holds only the loop's render and
blit and the call, and the readback and clear run only before and after the rounds. LATENCY-0's instrument is still a
byte-exact prefix. `allocreuse1-lock` was re-pinned on purpose for this court's two fresh-reference call sites (its
witnesses compare the loop with the fresh path).

**First host attempt: refused, no number.** On the owner's host the court refused PRESENTEXACT-READBACK-STALE before
any clock: after the window was cleared to white, the composed screen under it did not read back as white. The
geometry check had passed (a 1920×1080 client at (0,0) on a 1920×1080 screen). This is the refusal the method
registers for anything over the window or any transform of its pixels, and it says only that the readback does not
yet see the window exactly. A diagnostics patch followed, changing no method. The refusals now say where the pixels
differ (how many, their bounding box, and the first one's bytes). `shell presentexact-probe` (window build only: no
clock, no court, no record) repeats the court's clear-and-read-back, then varies one suspect at a time: a longer wait,
the z-order and foreground re-asserted, the cursor hidden. Each time it reads back both the composed screen and the
window's own surface, and it can save the images. Any fix the probe points to is a method change, so it would be
registered as an amendment before a number is taken.

**Diagnosed: a host overlay over every window (probe, owner's host; observed, not sealed).** The window's own surface
matched exactly in every step. The white clear, and sealed frame 0 under both calls, all read back exact. The composed
screen differed only inside one box, (1303,0)–(1748,27): 446×28 pixels at the top of the screen. That box is the host's
performance overlay, a translucent bar reading "1:09 am | APU 9W 67°C | BATT 100% | FPS …", which the compositor draws
over every window. It dims what lies under it to about 70% (white 255 read back as 179; frame 0's BGR (196,142,112)
read back as (138,100,79)), and its white text left 388 of the box's pixels unchanged on the white clear. So 12,100
pixels differed on the clear and 12,351 on frame 0. Re-asserting topmost and foreground changed nothing, and neither
did waiting 30 more compositions. Hiding the cursor changed the count by 38 pixels, because the overlay's own figures
had updated. **Outside that box the composed screen equalled the certified picture: the white clear, and frame 0 under
StretchDIBits and under SetDIBitsToDevice, with zero differing pixels.**

So the court refused for the reason its limits name: another window over the certified picture. The method is right
and needs no amendment. Measuring around the bar is excluded by the preregistration, and it would also be wrong,
because while the bar is on, the composed screen is not the certified picture. The owner switches the overlay off and
reruns the court unchanged. What PRESENTATION-CHOICE-0 can promise is limited to what the shell controls: a host
overlay drawn over every window is outside it, and the readback makes such an overlay visible rather than hiding it.

**Measured, with the overlay off (host DANIELDILLBERG, `shell/attest/presentexact-DANIELDILLBERG.json` and
`presentexact-confirm-DANIELDILLBERG.json`, citing PRESENT-EXACT-0 `bc910e2f`, PRESENTATION-CHOICE-0 `4a7a32d9` and
HOST-STATE-0 `58250382`).** The owner switched off the vendor's real-time monitor, and the probe then read every step
back exact, with 0 differing pixels on the screen and in the window. Both court runs passed the geometry check (a
1920×1080 client at (0,0), the screen 1920×1080 logical and physical). Both passed the hard gate: **10 of 10 readback
checks per run, 62,208,000 bytes compared, 0 differing.** That covers the four sealed frames under each call after a
white clear, plus the last frame again after the rounds. 1000 samples per cell, ABBA, through the adopted
`LoopRenderer`. In µs:

| | first run: StretchDIBits | first run: SetDIBitsToDevice | confirmation: StretchDIBits | confirmation: SetDIBitsToDevice |
|---|---|---|---|---|
| **envelope p99 (the rule)** | **12,187** | **12,113** | **12,279** | **12,117** |
| envelope p50 / p95 | 10,047 / 11,662 | 10,212 / 11,637 | 10,203 / 11,619 | 10,139 / 11,688 |
| call interval p50 / p99 | 1,834 / 2,296 | 1,823 / 2,199 | 1,846 / 2,321 | 1,838 / 2,325 |
| frame-ready → composited p50 / p99 | 2,584 / 14,851 | 2,423 / 14,810 | 2,352 / 15,195 | 2,430 / 15,211 |

**The reading: NO MATERIAL DIFFERENCE, twice.** StretchDIBits' p99 was 1,006‰ and then 1,013‰ of
SetDIBitsToDevice's, and SetDIBitsToDevice's was 993‰ and then 986‰ of StretchDIBits'. Neither came within the 950‰
bound; the nearest was 36‰ away. So the preregistered adoption is **SetDIBitsToDevice**,
the simpler call, with no stretch path at all. The confirmation record states it. Measured refresh: 13,129 and
13,710 µs.

**Beside the reading, not ruled on.** At 1:1 the call itself took about 1.8 ms at p50 under either call. The whole
envelope (render, blit and call) was about 10.0–10.2 ms at p50, below the refresh. frame-ready → composited was therefore
short at the median (2.4–2.6 ms), with a p99 near one refresh. The half-size courts' envelopes (13.7–17.4 ms p50, with
a 7–8 ms blit) are a different window and destination. That is a cross-court difference, recorded and not interpreted.
The two runs were within 2% of each other at p50, and before both, HOST-STATE-0 recorded the same clock state and plan
and memory at 85–86% (`GHOSTS.md` G13). The owner reports bumping the mouse at the start of one run. The court records
no input count in its record. The cursor is not part of the screen readback, the checks after the rounds read back
exact, and the ABBA interleave spreads a brief disturbance over both calls. The nearest bound was 36‰ away in either
run, too far for a few disturbed samples in the first rounds to cross. So it could not plausibly have moved the
reading, and it is noted rather than hidden.

**Grade.** DECLARED: the method (hash-locked). ESTABLISHED (gate): the court's logic, the readback's refusals
(including a call that writes nothing) and the sealer's rule. MEASURED (host, two runs): the composed screen equalled
the certified picture on every checked frame under both calls (20 checks, 0 differing bytes), with the host overlay off.
No material cost difference between the calls, so **SetDIBitsToDevice is adopted**. This is the first check in the
program of what reaches the screen rather than what is handed to GDI. It holds on this host and screen, up to the
composed screen, and only while nothing draws over the window.

**does_not_show.** That the pixels reach the eye unchanged: the readback is the composed screen, before scan-out, the
panel and any display-side colour processing. That every timed frame read back equal: the readback runs on the sealed
frames before the clock and on the last frame after it. Anything about another screen size, scaling setting or GPU
driver. Input-to-photon.

**Falsifier.** `presentexact-fence` goes red if a second variable enters the present, the window or the timed
interval. `presentexact-sealer` goes red if a label fires anywhere other than where it was registered, if a p50
decides, or if a differing byte is accepted. `presentexact-court` goes red if a plant passes, including a call that
writes nothing. On the host, one differing byte, a stale clear, a wrong geometry or a closed window yields no number.

## PRESENT-EXACT-0 LOCK — the conforming presenter: `shell show`, 1:1, SetDIBitsToDevice, the screen read back (seat 25)

**What is locked.** PRESENT-EXACT-0 read the composed screen back exact under both calls and found no material cost
difference, so its preregistered adoption is SetDIBitsToDevice. This rung carries out that adoption and gives
PRESENTATION-CHOICE-0 a shipped implementation. `shell show --level L --tiles T --camera x,z,F` shows one certified
frame. `shell show-playback --session S` shows a sealed session's frames, with SHELL-PLAYBACK-b's dwell, holding the
last one. Both render before the window opens: one compose for `show`, the owned pre-render for `show-playback`. So the
shipped shell still runs no per-frame render loop (`GHOSTS.md` G12).

**How it presents.** Every frame is guarded by the blit-hash law before any window opens. Then the process goes
DPI-aware, and the borderless, topmost 1920×1080 window opens at (0,0). The geometry is checked, and a screen that
cannot hold the whole frame 1:1 refuses with SHELL-SHOW-GEOMETRY. Frames go out through the same surface the court
witnessed, with the call fixed at SetDIBitsToDevice. **After every present the composed screen is read back** and
compared with the certified bytes: after each new frame, and about once a second while a frame is held. Each new frame's
result is printed, and a held frame's only when it changes. On a mismatch the presenter says where (pixel count, box,
first bytes), **keeps showing** (the owner's choice), and exits with code 3 at close instead of 0. The bytes it hands
over stay certified; only the on-screen claim is withheld, and it says so. Esc or Alt+F4 closes it. It takes no clock
and writes no record. `run` and `playback-window`, LATENCY-0's frozen half-size windows, are unchanged.

**The fence (row `presentexact-lock`).** The presenter is fixed to SetDIBitsToDevice through the witnessed surface,
with no StretchDIBits and no call switch. It guards the blit law, goes DPI-aware, opens the window and checks the
geometry, in that order, before its first present. Every present is followed by a screen readback, and the exit code
is non-zero when one differed. Its window is the borderless topmost popup at (0,0) and closes on Esc. It writes no
record and reads no clock. `show` and `show-playback` dispatch to it, and `run` and `playback-window` did not move. A
windowless build refuses both commands (SHELL-NO-WINDOW). Where the checkout carries the two host records (the owner's
does), they must be the pinned ones (`2eee8efc`, `7af3b71a`), read the screen exact and adopt SETDIBITSTODEVICE.
`allocreuse1-lock` was re-pinned on purpose for the presenter's blit-law guard.

**A fence tightened after review.** In the first version of this patch only the first present refused on failure.
The later presents (each new playback frame, and each held-frame re-check) discarded the result, so a failed present
could have been followed by a readback of the *previous* screen, which would have passed as a witness of a frame
never presented. Now every present goes through `show_present`, which refuses (SHELL-SHOW-NO-PRESENT, exit 2) when
the present fails, and each is followed at once by its readback. `presentexact-lock` checks that the section has
exactly one present call, inside that helper, and that every helper call is immediately followed by a readback.

**First host use (owner's host; observed, not sealed).** `shell show` on the witness view: 296 screen readbacks, 0
differed, exit 0. `shell show-playback` on the sealed session: 4 frames, each "the screen is the certified picture",
37 readbacks, 0 differed, exit 0. These are a viewer's own reports, not a court's number, and they are recorded here as
observations only.

**Grade.** ESTABLISHED (gate): the presenter's structure, its fixed call, every present refusing on failure and
followed at once by its readback, and its refusals. MEASURED (PRESENT-EXACT-0, host, two runs): the composed screen equalled the certified picture on every
checked frame under the adopted call, with the host overlay off. What `shell show` itself reads back on a given run is
printed by that run and not sealed: it is a viewer, not a court.

**does_not_show.** What reaches the eye: the witness ends at the composed screen. That an overlay, notification or
colour transform will not appear: the presenter reports it rather than preventing it. Any screen other than 1920×1080 at
100%. A live loop: `show` does not render per frame; that is the live-loop rung's own court, and it will enter through
`LoopRenderer`.

**Falsifier.** `presentexact-lock` goes red if the call can change, a present can fail without a refusal, a present
goes unread or is not read at once, the exit code hides a mismatch, the window stops closing on Esc, the blit law moves after the window, the frozen windows move, or the host
records are not the pinned exact-screen pair.

## REFUSAL-WHY-0 — why a screen readback refused: the windows above ours over the differing box (an apparatus; landed)

**Why.** PRESENT-EXACT-0's first host run refused at its readback, and the refusal could say only *that* the screen
differed and where. Naming the cause took a separate probe run and the owner's knowledge of the host (a vendor's
real-time monitor overlay, a translucent bar drawn over every window). REFUSAL-WHY-0 puts that second step into the
refusal itself. **It is explanatory apparatus, never a correctness dependency.** It runs only after a verdict is
decided and cannot change one.

**The method (`15701718`).** When a screen readback differs, the message already gives the pixel count, the box and the
first differing bytes. After that decided text it now appends an attribution. It walks the top-level windows in the Z
order from the top down to ours (`GetTopWindow`, then `GetWindow(GW_HWNDNEXT)`). For every window that is visible, not
cloaked (`DWMWA_CLOAKED`: another virtual desktop or a suspended app is not composed) and whose rectangle meets the
box, it names the owning program's image, the process id, the class, the title, the rectangle, and the extended styles
an overlay usually carries (topmost, layered, click-through, tool window, no-activate). At most six are named. If none
meets the box, it says the cause is below the window layer: a compositor-level overlay, a colour transform, or pixels
drawn outside any window. It uses read-only queries only. A process is opened with limited query rights, just to read
its image name. It moves, shows, activates, closes, messages and terminates nothing. The attribution appears on
the court's two readback refusals (READBACK and READBACK-STALE), on `shell show`'s mismatch lines, and on the probe's
screen line. The presenter decides and counts a mismatch before it names one. (It named it only on the lines it
printed until REFUSAL-WHY-1, which walks once per differing readback so the refusal log can carry the result.) The court's hook is a trait method whose default names nothing, so a surface without it keeps its old message.

**Rows.** `refusalwhy-preregistered`: the method is locked, and the code stops at the registered six windows.
`refusalwhy-fence`: the section is appended after the presenter's. It declares exactly ten read-only imports, opens
processes with limited query rights only, and contains none of the calls that act on a window or process. The
attribution is reached from three places only: the exact surface, the presenter's mismatch line and the probe. In the
court both refusals call it after their decision and only append it, and the presenter's verdict and count come before
it. PLANTS on the mock court: a changed byte, and a new plant, a clear that writes nothing. Each still refuses with no
record, and its message carries the mock's attribution after the decided text, over the same box the message
describes.

**Grade.** DECLARED: the method. ESTABLISHED (gate): the order (decision first), the read-only surface, the append-only
message, and the refusals unchanged under the mock. NOT_MEASURED (host): no refusal has met the attribution on a host
yet. The next one will carry it.

**does_not_show.** That a named window caused the difference: a candidate, never a cause. The instant of the readback:
the Z order and rectangles are read just after it, so a window that moved or closed in between can be missed or named
wrongly. Child windows, the cursor, or anything below the window layer: "below the window layer" is where the walk
stops, not a diagnosis. An elevated or protected owner's image name (it reads as unreadable).

**Falsifier.** `refusalwhy-fence` goes red if the section acts on a window or process, declares another import, opens
a process with more rights, is reached from a fourth place, is called before a decision or used for more than the
message, if the default names something, or if a planted refusal stops refusing or names a box other than its own.

## HOST-STATE-1 — the clock the OS computes, and paging, recorded beside HOST-STATE-0 (an apparatus; landed, first host look taken; no court records it yet)

**Why.** HOST-STATE-0's MHz is what `CallNtPowerInformation` reports. On the owner's host it never exceeded 2,000,
limit included, so it cannot say whether the clock differed between two runs. HOST-STATE-0 also records nothing about
paging, while G13's slower run sat beside 96% memory load. HOST-STATE-1 adds the two witnesses those gaps call for.
**Record, don't control**, as before.

**The method (`b992d9dd`).** Version 2 of the snapshot is HOST-STATE-0's eight fields, unchanged and in order, then two
more, read through the performance-counter library (`pdh.dll`) by their English names, so the paths do not depend on
the display language. `clock` is `\Processor Information(_Total)`'s Processor Frequency (the nominal MHz), %
Processor Performance and % Processor Utility, uncapped because both exceed 100% under boost, recorded as permille. It
also records the effective-MHz estimate that the OS's own arithmetic gives: nominal × performance. `faults` is
`\Memory`'s Page Faults/sec, Page Reads/sec (hard faults) and Pages Input/sec. Each field takes its own 1000 ms
window, so a version 2 snapshot takes about three seconds. Each counter stands on its own: one that cannot be added or
formatted is recorded as unavailable with its PDH status. **Version 1 stays the default** of `capture`, `capture_safe`
and `diagcommon.host_run`, so ALLOC-REUSE-1 and PRESENT-EXACT-0, which cite HOST-STATE-0, record exactly what they
recorded before. A court records version 2 only when its own preregistered entry says so. `python verify/hoststate.py`
now prints a version 2 look and writes nothing.

**Rows.** `hoststate1-preregistered`: the method is locked. The code's fields, counters, window and format, and the
version 1 default, equal the registered ones. `hoststate1-record`: the default snapshot is still HOST-STATE-0's shape
and markers, exactly. Off Windows every version 2 field is unavailable, and the Windows path degrades field by field.
Clock's estimate is nominal × performance, needs both, and a failed counter stands alone. Well-formed snapshots of both
versions validate. A mislabelled, mixed, float- or boolean-bearing, or unknown-version snapshot becomes an unavailable
snapshot of its version. No court asks for version 2. The recorder calls only PDH's reading functions.
`hoststate-record` still holds for the whole source (no control API, no file written, one query command).

**First host look (DANIELDILLBERG; one snapshot, nothing written).** The patch applied, the gate read 133 rows twice,
byte-identical, and every counter read. `clock`: Processor Frequency 1,658, % Processor Performance 1,185‰, % Processor
Utility 60‰, estimate 1,964. HOST-STATE-0's field in the same snapshot: `CallNtPowerInformation` current 1,610–2,000
(median 1,610), maximum and limit 2,000. `faults`: 1,708 page faults/s, 1 page read/s, 16 pages input/s. `memory`: 94%
load with 649 MB available. `load`: 67‰ busy.

Three observations, each from one second of one look. First, the OS reports delivered performance above nominal
(118.5%). The CallNtPowerInformation MHz, which never exceeded 2,000, could not show that. This is the gap HOST-STATE-1
was added to fill. Second, Processor Frequency read 1,658: below the 2,000 maximum, and inside the range of the
current values CallNtPowerInformation reported. So on this host that counter looks like a current frequency rather than
a constant nominal one, and the product the estimate takes is not established to mean an effective clock. Third, at
94% memory load, hard faulting was 1 page read/s. So a high memory load did not come with heavy paging in that second.
G13's association is with memory load, which is not the same thing as paging.

**Erratum (the entry is hash-locked and unchanged).** HOST-STATE-1's entry calls Processor Frequency "the nominal MHz"
and the estimate "nominal x performance". The first look does not support that gloss on this host (UNDERDETERMINED).
The arithmetic stays as registered, and the recorder's text now describes it literally: Processor Frequency x %
Processor Performance. A court that wants a clock witness should rule on neither: its own entry would say which
counter it records and what it takes each to mean. Also fixed after the host run: the recorder's docstring carried an
invalid escape (`\P`), which the host's Python warns on and the gate's older Python did not. Every `verify/*.py` is now
compiled on the gate with such warnings recorded (`hoststate1-record`).

**Grade.** DECLARED: the method. ESTABLISHED (gate): the shape, the unchanged default, the degradation, the
independence of each counter. MEASURED (host, one look): every counter reads on the owner's host. UNDERDETERMINED:
what Processor Frequency denotes here, and so what the estimate means.

**does_not_show.** A measured clock: % Processor Performance is the OS's ratio of delivered to nominal clock,
averaged over the window and every processor, and the estimate inherits that. The court's own paging: the rates are
system-wide. Anything inside the court's interval: each window is a second of the whole system around the snapshot.
Thermal state. A cause: association, never cause.

**Falsifier.** `hoststate1-record` goes red if the default snapshot changes, a court asks for version 2, a counter's
failure takes another with it, the estimate is computed otherwise, a bad snapshot is let through or mislabelled, or the
recorder calls a PDH function that is not a reading one.

## REFUSAL-LOG-0 — every refusal on the present path leaves one line (an observation; landed)

**Why.** A console line says that a refusal happened, once, to whoever was watching. Nothing keeps it. So the only way
to ask whether a refusal recurs is to compare transcripts by hand. REFUSAL-LOG-0 makes refusals accumulate: one line
per refusal event, appended to a log that is never rewritten, so that "the same reason, from the same place, in six
runs" becomes a count. **It is an observation about execution, never evidence and never authority.** It is not sealed,
not chained and not committed. No rule reads it, and nothing on the present path reads it back. The console stays
exactly as it was.

**The method (`424b7c9a`).** The admitted operations are the PRESENT-EXACT-0 court and the locked presenter.
The court now returns its refusals as data (`presentexact::Refused`): an attribution, a small context and the message,
unchanged. It builds them and writes nothing. They are logged where they are emitted, by the headless selftest and by
the host window. The presenter (`show`, `show-playback`) logs each of its refusals, and **each completed screen
readback whose pixels differ from the presented certified frame** (the owner's grain: one record per differing
readback, so the log's count equals the run's `differed` count, and a mismatch held under an overlay adds about one a
second). One primitive does the writing (`shell/refusallog.rs`). `refuse` appends the record and then prints the
console line, so a refusal cannot print without leaving its line. `record` is the same append, used once in the
presenter, for a differing readback that has already been decided and counted. A record is one JSON line with these
fields: `refusal_id` (`run_id/seq`), `run_id` (the process's start and id), `seq` (monotonic within the run),
`unix_ms`, `operation`, `surface` (`mock` or `gdi`), `reason_code` (the refusal's console code), `attribution` (a fixed
token from a registered vocabulary, such as `present.readback` or `clear.readback`, never a prose diagnosis), `context`
(integers and strings: the frame, the call, the differing bytes, the box) and `context_digest` (the context's sha256).
It is written to `$VERDANDI_REFUSAL_LOG` if that is set, otherwise to `build/refusals.log` under the working directory,
which is gitignored. A log that cannot be written is said on the console (`SHELL-REFUSAL-LOG-UNWRITTEN`), and the
refusal goes on unchanged. The gate points the variable at its own scratch file, so its planted refusals never reach
the owner's log. `python verify/refusallog.py` validates the log and counts it by operation, surface, reason and
attribution, with the number of distinct runs. It writes nothing.

**Rows.** `refusallog-preregistered`: the method is locked, and the variable, default path and record keys are the same
in the shell and the reader. `refusallog-bijection` executes the one-to-one invariant on the mock court. A clean run
adds no record. Each of the six plants refuses once and adds exactly one record, with the printed code, the
registered attribution, and `run_id/seq`. The log only grows. Without the variable, the record goes to
`build/refusals.log` under the working directory. An unwritable log is said, and the refusal's exit status and message
are byte-identical. `refusallog-fence`: every refusal the court returns is data with a registered attribution, and the
court writes nothing. Both emission points log before they exit. In the presenter, all six refusals print through the
primitive, each before its own exit, and the one differing-readback record comes after the count. The writer only
appends. Nothing else in the shell or in the sealers names the log, and the gate's variable points into
`verify/build`. `refusallog-reader`: a tampered digest, a missing or extra key, a float, a wrong `refusal_id`, a
non-JSON line and a skipped `seq` are each reported and not counted. The command prints the counts and leaves the log
unchanged. 29 mutations of the writer, the court, the presenter, the reader and the gate's isolation were each caught.

**On the owner's host.** After two full gate runs, `python verify/refusallog.py` read `build\refusals.log` as
absent: the gate's planted refusals went to its own scratch file, not into the owner's log.

**Grade.** DECLARED: the method. ESTABLISHED (gate): the one-to-one invariant on the court, append-only growth, the
default path, the unchanged refusal under a failed append, the reader. ESTABLISHED (source): the presenter's call sites.
ESTABLISHED (host): the gate's isolation. NOT_MEASURED (host): no host refusal has been logged yet.

**does_not_show.** Why a refusal happened: a count is not a cause. That a refusal cannot occur: zero records is not
proof. Refusals outside the admitted operations: argument errors, the windowless build, and the host window court's
harness (the shared DWM prelude and the window's creation, before the court function starts). The presenter's records
executed on the gate: `show` needs a window, so its call sites are fenced from the source. A record whose append failed
(the console says so). Timing: `unix_ms` is the wall clock, for grouping only.

**Falsifier.** `refusallog-bijection` goes red if a refusal prints without a record, leaves two, or leaves one that does
not match its printed code and registered attribution; if the log is rewritten; or if a failed append changes the
refusal. `refusallog-fence` goes red if a presenter refusal bypasses the primitive, the court writes or prints its
own refusal, the writer can truncate, anything else names the log, or the gate stops isolating its own refusals.

## RUN-LEDGER-0 — one line per run, refused or not: the refusal log's denominator (an observation; landed)

**Why.** The refusal log holds refusals only. A run that refused nothing leaves no trace in it, so "no refusals
occurred" cannot be told from "the run was not recorded", and a recurrence can only be stated as "N runs that
refused", never as "refused in N of M runs". RUN-LEDGER-0 records the runs. It is kept in a file of its own, so every
line of the refusal log is still a refusal.

**The method (`ecf3fdb9`).** When an admitted run ends, whatever its outcome, one JSON line is appended to
`$VERDANDI_RUN_LEDGER`, otherwise `build/runs.log` (gitignored). The line holds `run_id` (the refusal log's, so the two
files join on it), `operation`, `surface`, `readbacks_checked` and `differed` (the operation's own counts of compared
screen readbacks, counted exactly where it counts them), `refusals` (how many refusal records the run emitted),
`exit_code`, `unix_ms_start` and `unix_ms_end`. A court run begins just before the court function and ends with the
court's outcome, at both emission points (the selftest and the host window). A presenter run (`show`,
`show-playback`) begins on entry and ends immediately before each of its seven exits, with that exit's code. A clean
run is a line with `differed` 0 and exit 0. A failure before the run begins (a usage error) is not a run and appends
nothing. Like the refusal log, the ledger is not sealed, not chained, not committed and read by no rule. A ledger that
cannot be written is said on the console (`SHELL-RUN-LEDGER-UNWRITTEN`), and the run goes on unchanged. The gate points
the variable at its own scratch file. `python verify/runledger.py` validates the ledger, counts runs by operation,
surface and exit code with their readbacks, and joins it to the refusal log. It writes nothing.

**Rows.** `runledger-preregistered`: the method is locked, and the variable, default path and line keys are the same in
the shell and the reader. `runledger-bijection` runs the mock court's clean run and its six plants. Each appends exactly
one line, with the process's exit status and the court's own readback counts. The clean run reads 10 checked and 0
differed, equal to its raw record's readback checks. The plants read the counts the mock makes exact (a changed byte:
1 checked, 1 differed; a call that writes nothing: 2 and 1; a mid-court close: 8 and 0). Each line's refusals equal
the refusal records carrying its `run_id`. A usage error appends to neither file. The ledger only grows, the default
path holds, and an unwritable ledger leaves the run's exit status and output byte-identical. `runledger-fence`: the
begin and end points are where the operations begin and end, and every presenter exit is immediately preceded by an
end with its own code. Readbacks are counted only where the court and the presenter count their own. The two files
never write into each other, and nothing else names the ledger. `runledger-reader`: malformed, inconsistent and
repeated lines are reported and not counted. The join reports a claimed refusal the log lacks and a refusal with no
ledger line. The command changes nothing. 22 mutations were each caught.

**On the owner's host.** After two full gate runs, `python verify/runledger.py` read `build\runs.log` as absent: the
gate's runs went to its own scratch ledger. Then the first ledgered host run: `shell show` on the witness view, run as
the overlay check. It printed 94 screen readbacks, 0 differed, and exited 0. The ledger's line read `show gdi exit=0
readbacks=94 differed=0`, matching the console, and the refusal log stayed empty, as it should with nothing differing.
No readback differed, so the refusal half of the join was not exercised on the host. Whether the overlay was on and
above the window during that run was not recorded.

**Grade.** DECLARED: the method. ESTABLISHED (gate): one line per run on the court, its counts, the join, append-only
growth, the default path, the unchanged run under a failed append, the reader. ESTABLISHED (source): the presenter's
begin and end points. ESTABLISHED (host): the gate's isolation, and one clean presenter run ledgered with the console's
counts. Since DRIFT-0 began, court runs too: each sealed DRIFT-0 run joined to exactly one court line with the court's
10 readbacks. NOT_MEASURED (host): a refused or differing run.

**does_not_show.** A rate as a cause. That a clean run proves a refusal cannot occur. Runs outside the admitted
operations. A court run's raw-record write: its line records the court's outcome, so a later write failure exits 2
after a line that says 0. A process killed from outside: it ends without a line, and the ledger cannot say so.

**Falsifier.** `runledger-bijection` goes red if a run leaves no line or two, a line's exit code, counts or refusals
disagree with the run, a usage error appends a line, the ledger is rewritten, or a failed append changes the run.
`runledger-fence` goes red if a presenter exit is not preceded by its end, a readback is counted anywhere else, or the
two files write into each other.

## REFUSAL-WHY-1 — the covering windows written into the refusal log (an apparatus; landed)

**Why.** REFUSAL-WHY-0 names the windows above ours over a differing box on the console, once. The refusal log keeps
refusals but not what covered the screen. So "the same overlay, in six runs" still meant reading transcripts.
REFUSAL-WHY-1 writes the same walk's result into the record, so the log accumulates it. Like REFUSAL-WHY-0, it is
explanatory apparatus, never a correctness dependency.

**The method (`ac75db51`), under the owner's rule.** After the verdict is decided and counted, a screen-readback
record (the court's READBACK and READBACK-STALE, and each of the presenter's differing readbacks) carries these fields
after its own context: `covering_layer` (`windows`: a window above ours meets the box; `below`: none does, so the cause
is below the window layer; `unplaced`: our window was not found in the Z order), `covering_count`, and, for each window
named (at most six), `window_N_program`, `window_N_class`, `window_N_flags` and `window_N_rect`. **Titles are never
persisted.** They may appear on the console, but they never enter the log, and neither do process ids. The rectangle is
diagnostic geometry, not identity, so the grouping key is program, class and flags. One walk serves both the console's
words and the log's fields: `seen_text` renders REFUSAL-WHY-0's line unchanged, and `seen_context` builds the fields
without reading a title or a pid. The presenter now walks once per differing readback, after it is counted and before
it is recorded, and prints from the same walk. `python verify/refusallog.py` now also counts covering windows by layer
and by program, class and flags, with the runs each came from.

**Rows.** `refusalwhy1-preregistered`: the method is locked, and the code's window fields are the registered four, six
times. `refusalwhy1-log`, on the mock court: the changed byte, the call that writes nothing and the clear that writes
nothing carry the layer and count after their own context, with the refusal unchanged. A new plant places a synthetic
overlay window, with a title, over the changed byte. Its console line names the window's program, pid, class, title
and flags. Its record carries program, class, flags and rectangle, and neither the title nor the pid appears anywhere
in the log. Refusals that are not screen readbacks carry no covering fields. The reader counts the overlay by program,
class and flags. `refusalwhy1-fence`: the fields are built only by `seen_context`, which reads no title and no pid. The
host surface and the presenter take words and fields from one walk. The presenter passes the fields only through its
context, and the probe never writes to the log. `refusalwhy-fence` was updated to the one-walk shape and still holds
REFUSAL-WHY-0's order and read-only surface. 12 mutations were each caught.

**Grade.** DECLARED: the method. ESTABLISHED (gate): the fields and their order, no title or pid in the log, the
refusal unchanged, the reader's counts. ESTABLISHED (source): the presenter's single walk. NOT_MEASURED (host): no
host refusal has carried covering fields yet.

**does_not_show.** That a named program caused the difference: a candidate, never a cause. Identity: image and class
names can repeat across unrelated programs, so a group is a candidate kind of overlay. The instant of the readback:
the Z order is read just after it. An owner that cannot be queried reads as unreadable, and all such owners group
together.

**Falsifier.** `refusalwhy1-log` goes red if a title or a pid reaches the log, a readback record loses its fields or
carries them before its own context, a non-readback refusal carries them, or the reader keys on the rectangle.
`refusalwhy1-fence` goes red if the fields read a title or a pid, a surface walks twice, or the probe writes to the log.

## DRIFT-0 — what variation is present within a run and between runs of the same workload (observational; sitting 1 of 3 complete)

**Why.** Twice a preregistered second run has been 40–60% slower than its first (G13), and no court has yet measured
by design how the same workload varies across runs. DRIFT-0 is that measurement. It is observational: no intervention,
no rule, no verdict, no threshold. It answers only what variation is present, within a run and between runs.

**The method (`d445dcf9`), as the owner ratified it.** The workload is the locked PRESENT-EXACT-0 court, **unchanged**:
the same shell command and flags, both calls, 1000 samples per cell, ABBA after 10 warm-up rounds, and the composed
screen read back before and after, checked by PRESENT-EXACT-0's own sealer check. DRIFT-0 changes repetition and
observation, not the workload. That keeps apparatus continuity: any variation it sees is the admitted presenter's, not
a new instrument's. The live loop gets its own court later. The design is 3 sittings of 4 completed runs. Runs within
a sitting are at least 60 s apart, and sittings at least 4 hours apart. The owner declares the overlay state for each
run (on, off or unknown; recorded, not verified). HOST-STATE-1's version 2 snapshot is taken just before and just after
each run; DRIFT-0 is the first court to record it. `python verify/drift.py --host NAME --sitting N --overlay off`
enforces the protocol before a run starts (sitting order, four completed runs each, both spacings) and never reads a
number to decide. A completed run is sealed as `shell/attest/drift-<host>-s<S>-r<R>.json`, with the workload's numbers,
exactly as PRESENT-EXACT-0's sealer derives them, and the within-run spread per call (p95 − p50 and p99 − p50, in µs
and in ‰ of the p50). A run whose court refuses is sealed as `drift-<host>-s<S>-x<K>.json`: kept, never discarded, and
not counted toward the sitting's four. `python verify/drift.py --host NAME --report` prints the panel and writes
nothing. It shows every run with its within-run spread, its host state, and the run-ledger line and refusal records
inside its time window. Then, per call, it gives the between-run spread of p50 and p99 (min, lower median, max, range,
and range in ‰ of the median) within each sitting, across all completed runs, and across the sittings' medians. The
two sealed PRESENT-EXACT-0 runs are shown beside it as history, never pooled.

**Rows.** `drift-preregistered`: the method is locked, and the sealer's design constants equal the registered ones.
`drift-sealer`, on synthetic runs: a completed run carries PRESENT-EXACT-0's own derivation, the within-run spread,
the protocol and the host state. It cites DRIFT-0, PRESENT-EXACT-0 and HOST-STATE-1, and holds no label. The host state
moves nothing. The workload's check still refuses what it refuses. A refused run seals with no numbers. The protocol
holds the sitting order, four completed runs each, and the two spacings, counting refused runs for spacing but not for
completion. `drift-report`, on 12 synthetic runs, a refused run, a ledger, a refusal log and history: the panel says
what it must, including the refused run's covering window. It joins each run to its one ledger line, carries no
verdict word, and the command writes nothing. `drift-fence`: the sealer never reads PRESENT-EXACT-0's rule, runs the
unchanged court command at 1000 per cell with HOST-STATE-1, and has a protocol that reads no number. Only the report
reads the shell's logs, the shell holds nothing of DRIFT-0, and `CourtRefused` marks only a window court's refusal.
17 mutations were each caught.

**Sitting 1, complete: four runs (DANIELDILLBERG; observations, not a reading).** Each run completed, read the screen
back exact (10 checks, 0 differing bytes), was sealed and committed by the owner with the overlay declared off, and
joined in the report to exactly one run-ledger line (exit 0, 10 readbacks, 0 differed, 0 refusals). These are the
first court runs in the host's ledger. An attempt at a fifth run was refused before it started (`DRIFT-FULL`), so it
left no record and no ledger line. That is the protocol holding on the host. The numbers, in µs, with the refresh
period the court measured and a few fields of the before-snapshot, as the owner's panel printed them:

| run | SetDIBitsToDevice p50 / p95 / p99 | StretchDIBits p50 / p95 / p99 | refresh | before: busy, perf, hard faults/s, available |
|---|---|---|---|---|
| s1 r1 | 10,146 / 12,147 / 13,139 | 10,085 / 12,220 / 13,335 | 13,270 | 112‰, 1,644‰, 179, 613 MB |
| s1 r2 | 9,591 / 10,973 / 11,638 | 9,642 / 11,085 / 11,629 | 12,445 | 20‰, 1,058‰, 3, 524 MB |
| s1 r3 | 9,450 / 10,888 / 11,461 | 9,407 / 10,950 / 11,492 | 13,566 | 26‰, 978‰, 0, 522 MB |
| s1 r4 | 10,583 / 12,777 / 13,574 | 10,506 / 12,864 / 14,388 | 13,675 | 15‰, 1,444‰, 448, 558 MB |

Within sitting 1, the p50 ranged 9,450–10,583 for SetDIBitsToDevice (range 1,133, 118‰ of the lower median 9,591) and
9,407–10,506 for StretchDIBits (1,099, 113‰). The p99 ranged 11,461–13,574 (2,113, 181‰) and 11,492–14,388 (2,896,
249‰). The within-run p99 − p50 ran 2,011–2,993 for SetDIBitsToDevice and 1,987–3,882 for StretchDIBits, with lower
medians of 2,047 and 2,085. The measured refresh period ran 12,445–13,675 (range 1,230; nominal 75 Hz is 13,333).

Runs 1 and 4 are the slower pair: p50 above 10,000 and p99 above 13,100 on both calls, and the widest within-run
spreads. Runs 2 and 3 are the faster pair: p50 below 9,700 and p99 below 11,700. Run 4 also shows a longer call interval
at p50 (2,321–2,325 against 1,793–1,887 in runs 1–3). Beside the pairs, the before-snapshots show two things. The slower
pair's show the highest performance ratios (1,644‰ and 1,444‰ against 978‰ and 1,058‰) and the most hard faults (179
and 448 a second against 0 and 3). CPU busy does not follow the pairs: 112‰ and 15‰ for the slower pair, against 20‰
and 26‰. The after-snapshots show neither pattern (performance 872–1,114‰, hard faults 0–4 a second in all four).
Memory load stayed at 94–95% throughout. Runs 2 and 3 sit below both earlier PRESENT-EXACT-0 runs at p50 and p99; runs
1 and 4 sit above them at p99. Processor Frequency read 1,634–1,878 across the snapshots, consistent with HOST-STATE-1's
erratum.

**What "just before" contains (a fact about the apparatus, recorded now).** The before-snapshot is taken by
`diagcommon.host_run` right after DRIFT-0's own steps: the shell is rebuilt with `rustc` and the headless selftest runs,
and only then is the snapshot taken and the window court started. Its load, clock and faults are three successive
one-second windows. So a before-snapshot's hard faults and clock may carry the build's and the selftest's, not an idle
host's. That is why the association above is between a run and what immediately preceded it, and is no more than that.
All of this is recorded, not read: four runs, association never cause, and the panel is DRIFT-0's answer only at 12.

**A display added to the panel (after sitting 1 closed, at the owner's request).** The report now shows each run's
measured refresh period, and its between-run spread within and across sittings. Every record already seals that
value. No record, rule, protocol step or registered report content changed. `drift-report` checks the new lines on
its synthetic runs, and three mutations of them were each caught.

**Grade.** DECLARED: the method. ESTABLISHED (gate): the sealer, the protocol, the panel and the fence. MEASURED
(host, partial): sitting 1, 4 of the 12 runs, as recorded above. ESTABLISHED (host): the protocol's refusal of a fifth
run in a full sitting. NOT_MEASURED (host): sittings 2 and 3.

**does_not_show.** Anything beyond this host, this screen, this workload and these runs. The within-run spread
between the recorded percentiles: the court keeps no raw samples. That a host state or a declared overlay caused a
variation: association, never cause. A verdict of any kind.

**Falsifier.** `drift-sealer` goes red if a record carries a label or a changed derivation, the host state moves a
number, or the protocol lets a run through too soon, out of order, or past a full sitting. `drift-report` goes red if
the panel's spreads, joins or history are wrong, or if it says a verdict. `drift-fence` goes red if the workload
changes.

## LIVE-LOOP-0 — the first per-frame loop: the sealed session walked live (measured on the host: the first live walk exact)

**Why.** Everything the shell has shown so far was rendered before its window opened, so the studio has been a
viewer. LIVE-LOOP-0 is the first loop that renders every composition live from the current state. It is the first
gate on the owner's route to a live, authorable world, and its first court is deliberately narrow: the loop itself.

**The method (`65550cc0`), as the owner ratified it.** The state comes from the sealed session, stepped live: 24
compositions per step (show-playback's dwell), then the last step held for 150 compositions, after which the run ends
by itself. Every composition is rendered through the adopted `LoopRenderer` from the current step and presented by
SetDIBitsToDevice, through the exact surface PRESENT-EXACT-0 witnessed, in the presenter's borderless 1920×1080 window
at (0,0). Nothing is pre-rendered for presentation. The witnesses come first, outside the loop: the geometry, then
each step's fresh reference reproducing its sealed witness. Those verified bytes become the step's expected bytes.
Inside the loop, every composition's frame is compared with them before it is presented; a difference refuses
(LIVELOOP-BYTES), because it means the renderer drifted. The composed screen is read back on the first composition of
every step and every 75th composition of the hold. A differing screen is counted, logged once in the refusal log with
its covering windows, and the loop goes on, as `show` does; it is not hidden and not a refusal. There is no authoring
input, no camera control, no clock, no flip model and no persistent worker; Esc or close aborts. The loop reads the
sealed session and writes nothing canonical: the session file's hash is taken before and after the run and must be
equal. Refusals are logged and runs are ledgered as the operation `liveloop`. On the host, `python verify/liveloop.py
--host NAME` seals `shell/attest/liveloop-<host>.json` with the counts only.

**Rows.** `liveloop-preregistered`: the method is locked, and the shell's and the sealer's constants equal the
registered ones. `liveloop-court` runs the same loop headless over the mock on every gate, so unlike `show` the loop
is executed, not only fenced. It walks 4 steps: 246 compositions, each rendered, byte-checked and presented, and 6
screen readbacks, none differing. The session file is unchanged, and the run is sealed. PLANTS: a tampered witness, a
mid-walk close and a client below a title bar refuse with no record. A present that writes nothing completes with all
6 readbacks differing, each counted, logged with its covering fields, and ledgered. Every refusal and every differing
readback is one refusal-log record, every run one ledger line, joined one to one. `liveloop-sealer`: the registered
walk seals and says whether the screen was exact, or how many readbacks differed. Twelve malformed walks are refused:
counts, readbacks, a changed session, the geometry, the call, the entry and the dwell. `liveloop-fence`: the witnesses
come before the walk. Inside it, the LoopRenderer renders the current step, its bytes are checked, and they are
presented, in that order. The call is fixed, and the loop takes no clock and writes no file. The host window is the
presenter's DPI-aware borderless window, with Esc or close only and the ledger around the loop, and a windowless build
refuses it. The fresh-entry pins now include `liveloop.rs`, on purpose, for its witnesses. `presentexact-lock` and
`refusalwhy-fence` now bound their win32 sections at the next section rule, so the new appended section is judged by
its own fence. 13 mutations were each caught.

**The first live walk (DANIELDILLBERG).** After the gate read 152 rows twice, identical, `python verify/liveloop.py
--host DANIELDILLBERG` built the window shell, passed the headless check, and walked the sealed session's 4 steps
live in the borderless window. There were 246 compositions, each rendered through the LoopRenderer from the current
step, byte-checked against the step's verified bytes and presented by SetDIBitsToDevice. All 6 screen readbacks were
exact (0 differed), and the console printed its single line, "the screen is the certified picture". The session file
was unchanged. The run was sealed as `shell/attest/liveloop-DANIELDILLBERG.json`, citing LIVE-LOOP-0 (`65550cc0`), and
committed by the owner. For the first time, the shipped shell rendered every composition live from the current state
and the screen showed exactly what it rendered at every readback.

**Grade.** DECLARED: the method. ESTABLISHED (gate): the loop, executed over the mock, its plants, its logging and
ledgering, the sealer and the fence. MEASURED (host, one walk): 246 compositions rendered live and presented, 6 of 6
screen readbacks exact, the session unchanged.

**does_not_show.** Speed: counts only, no timing. What reached the screen between readbacks: the byte check covers what
the loop handed the call. A fresh present versus a stale one during the hold, since the loop does not clear between
compositions. Authoring, input or camera: the state is the sealed session's steps. Any other host or screen.

**Falsifier.** `liveloop-court` goes red if a composition is not rendered, checked and presented, a readback is
missed, a difference is hidden, stops the loop or goes unlogged, the session changes, or a plant stops refusing.
`liveloop-fence` goes red if a frame reaches the call without being rendered live from the current step, a clock or
input enters, or the window changes.

## LIVE-INPUT-0 — key presses feed the session the live loop renders: walk plus open/close (measured on the host: the live session walked and edited by key presses, every readback exact)

**Why.** LIVE-LOOP-0 rendered every composition live, but from a sealed session's fixed steps. LIVE-INPUT-0 is the
next gate on the route: physical input becomes typed events in the same session authority that the live renderer
consumes. The owner kept it narrow, walking plus opening and closing cells, and asked for one property above all: live
input feeds the same session authority that the live renderer consumes, with no world held by the shell beside it.

**The method (`f81c2cf1`), as the owner ratified it.** The binding is fixed. Up or W steps forward, Down or S steps
back, Left or A and Right or D turn, Q and E strafe (INPUT-0's six moves), Space opens or closes the faced cell, and Esc
ends the session. An auto-repeated press is counted and never bound, so one press is one action, because the repeat
rate is a host setting and a clock. Any other key is unbound and ignored. The faced cell is the cell one step ahead of
the camera, the same cell a forward step targets. Rock opens to floor (`cell:X,Z,.`), floor closes to rock
(`cell:X,Z,#`), and a stair is not toggled. There is no cursor, no mouse and no new view semantics, so the same camera
and the same press always address the same cell. Every action is appended as an event to an in-memory SESSION-WALK log.
An edit is validated as the workshop validates one (a border cell stays rock); a refused edit is one refusal-log record
and no event, and the loop goes on. W, M, the camera and the walk head are the replay of that log through the shell's
SESSION-WALK machinery in `shell/playback.rs`, using `replay_from`'s own statements (`step`, `apply_spec`,
`content_hex`, the `compose_frame` frame digest, `fold`). The replay advances one event at a time from the replay of
the log before it. That is a left fold, the checkpoint equivalence SHELL-PLAYBACK's rows already certify. The session's
state is private to that file: the loop appends events and reads the state, and cannot write W or M. After each event,
the new state's fresh reference is rendered once. For a move, it must reproduce the event's chain witness; otherwise
the loop refuses (LIVEINPUT-WITNESS), because it would render a state the chain did not witness. Every composition is
rendered through the `LoopRenderer` from the session's current state, compared with that reference (a difference
refuses) and presented by SetDIBitsToDevice in the presenter's borderless window. The screen is read back on the first
composition after every change and every 75th composition a state is held. Esc or closing the window ends the session
with exit 0. Nothing is saved: the log lives in memory and dies with the run, since persistence is LIVE-SESSION-0's.
Refusals are logged and runs ledgered as the operation `liveinput`. The host run writes no record.

**Rows.** `liveinput-preregistered`: the method is locked, and the loop's constants, its binding table and the faced
cell's two edits are the registered ones. `liveinput-binding` proves binding determinism. Two scripts run over the mock
with one press every 3 compositions. Script A, from 28,28,N, opens the faced cell and walks through it, takes a
blocked step, opens a cell and closes it with a turn away and back between, steps back, strafes both ways, is refused
at a stair, closes a cell and walks into it. It uses all six moves from both arrows and letters and passes an
auto-repeat and an unbound key on the way. Script B, from 46,14,E, is refused at the east border. All 31 presses become
exactly their registered outcomes at their registered compositions: 24 typed events in the expected order, the repeat
and the unbound key ignored, and the stair and the border refused as one refusal-log record each and no event. Every
composition is rendered, byte-checked and presented, the screen is read back once per change with no difference, and
each run is one ledger line, joined one to one. `liveinput-continuity` proves authority continuity. Each script's event
log is replayed headless through the workshop's own SESSION-WALK (`sessionwalk new`, one `move` or `edit` per event,
then `verify`), a separate implementation built on the kernel's reference picture. It reproduces every event's witness
and camera, the final camera, content and head the live loop reached, from the same genesis. W and M recomputed from
the level with the log's edits applied are the loop's. The state after each of the 4 edits recurs at a move with the
same W and camera, and the frame the loop presented after the edit has that move's workshop-certified frame digest.
The level and tiles files are unchanged. `liveinput-court`: a client below a title bar refuses with no raw output; a
present that writes nothing completes with all 3 readbacks differing, each counted and logged with its covering fields;
the clean short run reads the screen exact; a spent script is a normal end; an unknown key and a camera on rock are
refused before the run, with no ledger line. `liveinput-fence`: the session's state is private and changed only by
`push_move` and `push_edit_cell`, each replaying one appended event by `replay_from`'s statements. A repeat never
reaches the binding. A move's reference checks its witness. A composition is presses, then render, check, present and
read back, in that order. There is no clock and no file. The host window reads WM_KEYDOWN and its auto-repeat bit from
the message queue, is appended after LIVE-LOOP-0's section and writes nothing, and a windowless build refuses it. The
fresh-entry pins gain `liveinput.rs` (one reference render per change) and re-pin `playback.rs` (its session's move
witness is `replay_from`'s own digest), both on purpose. `runledger-fence` counts the new run and its readbacks. 26
mutations were each caught.

**The host runs (DANIELDILLBERG).** After 0068–0070, the gate read 157 rows (rowset `8acef41cd5c447c9`, the same as
in the container). The window shell was built with `--cfg shell_window` and run three times with `liveinput-window`,
each run starting a fresh session at 28,28,N over the frozen witness level. Nothing was written but the standing logs.
The consoles are the evidence; each walked log was replayed here through the workshop's `sessionwalk`.

*Run 1: no key press arrived.* The loop rendered 31,640 compositions live from the session's state through the
LoopRenderer, byte-checked each against the state's reference, and presented them by SetDIBitsToDevice. All 422 screen
readbacks were exact: 1 on the first composition and 1 every 75th held composition, the registered schedule for a state
that never changed. But keys, events, repeats and unbound were all 0. The session ended `closed`, not by Esc, and its
final state is the genesis: camera 28,28,N, content `390109b5…` (the base), head `73571153…`, the head `sessionwalk new`
gives for the same base. Why no press reached the window's queue is not established by the run. Keyboard focus is the
leading candidate: the window is topmost, so it sits on top whether or not it holds the keyboard, and Windows can
refuse `SetForegroundWindow` to a process started from a console. That remains a candidate, not a cause, because no
focus state was recorded.

*Run 2: keys arrived.* 29 presses, all moves, one of them blocked. The walk went east from 28,28 onto the stair cell at
34,28, back west to 24,28 and east again to 27,28. The loop presented 1,135 compositions, and all 37 screen readbacks
were exact. The session ended `closed`. Replayed through the workshop's `sessionwalk`, the 29 moves reproduce every
camera and head the console printed, ending at `3fe3d1b2…ed2`.

*Run 3: the deciding walk, protocol fixed beforehand.* The owner typed the gate's script A exactly, minus its one
auto-repeat (which makes no event), so 26 presses. The prediction, stated before the run, was: keys 26, unbound 1,
events 23 (19 moves and 4 edits), refused 1 (the stair), ended by Esc, camera 33,28,N, content `2769bf4f…`, head
`b73e983b…`. The run gave keys 26, repeats 0, unbound 1, events 24 (20 moves, 2 of them blocked, and 4 edits), refused
0 and ended by Esc. It presented 3,985 compositions with 65 screen readbacks, none differing. The final state was camera
32,28,N, content `ed0d3f18…` and head `ba350653b5693dadbf7ef33fe3d7d2d5c5e82913c04412b11c8010d34498e915`.

**The prediction was not met, and the divergence is located.** Presses 1 to 19 matched script A one for one. They
produced the same 18 events, with the same 18 heads that the gate's mock run of script A prints. Press 20 was S where
the script has SPACE, so the session stepped back from 33,28,E to 32,28,E instead of being refused at the stair. The
remaining presses then acted from a different place. LEFT turned north at 32,28, SPACE closed (32,27) instead of
(33,27), RIGHT and LEFT turned away and back, W walked into the cell just closed and was blocked, and Esc ended the
session. As the protocol required, nothing was repaired or reinterpreted; what was typed was replayed. Through the
workshop's `sessionwalk`, the 24 events reproduce every camera and head the console printed, and the final content and
head. The shell's own loop over the mock, fed the same 26 presses, prints the same 24 event lines and the same final
state and head as the host. Only the composition and readback counts differ, because those depend on when the presses
came.

**What the host runs show together.** Key presses reach the live session and become its events. A move changes the live
camera. Space produces typed edits that enter the session chain: (28,27) and (28,25) were opened, and (28,25) and
(32,27) were closed. An opened cell is walked through, and a closed cell blocks. Every composition was rendered from the
session's current state and byte-checked against that state's reference, and every screen readback was exact (37 of 37,
then 65 of 65, after the 422 of 422 of run 1). So the screen showed the state each edit and move produced. Esc ends the
session through its registered path. The session stayed the authority: the workshop's independent replay of each walked
log reaches the heads the loop printed. No refused edit happened on the host, because the deciding walk's 20th press
skipped the stair. The refusal path stays shown by the gate only, where both scripts exercise it.

**Grade.** DECLARED: the method. ESTABLISHED (gate): the binding on two scripts, the continuity through the workshop's
SESSION-WALK, the loop's refusals, logging and ledgering, and the fence. MEASURED (host, three runs): the input →
session → live loop bridge. That covers key presses becoming session events, moves and open/close edits entering the
chain, every composition rendered from the session's state and presented, every screen readback exact (422, 37 and 65),
Esc ending the session, and each walked log replayed by the workshop to the heads the loop printed. The deciding walk's
pre-stated head was not reached, because its 20th press differed from the script; the divergence is located, and the
walk as typed replays exactly. NOT_MEASURED (host): a refused edit. UNDERDETERMINED: why no key press reached the window
in run 1.

**does_not_show.** What reached the screen between readbacks: the byte check covers what the loop handed the call.
Presses between two compositions are all appended, but only the last state is presented. Holding a key does not walk.
Tiles, materials, a cursor, saving or recovering a session: LIVE-AUTHOR-0 and LIVE-SESSION-0. Timing or
input-to-photon latency. Any other host or screen. The host runs leave no record, only their consoles and the standing
logs: the evidence is the printed events and heads, replayed here.

**Falsifier.** `liveinput-binding` goes red if any press becomes anything but its registered outcome, a repeat or
unbound key makes an event, or a refused edit is appended or goes unlogged. `liveinput-continuity` goes red if the
workshop's replay of the live log disagrees with the loop in any witness, camera, the content or the head, or the frame
presented after an edit is not the one certified for its W and camera. `liveinput-fence` goes red if the loop holds or
writes a world of its own, takes a clock, writes a file, or the window changes.

## LIVE-SESSION-0 — the live session made durable and recoverable (measured on the host: a saved walk and its resumed continuation, each verified there and replayed here)

**Why.** LIVE-INPUT-0's host runs showed a working live loop, but its evidence was console text that had to be replayed
by hand, and the deciding walk's single typo could only be found by reading that text. The owner moved LIVE-SESSION-0
ahead of LIVE-AUTHOR-0, so that every later host walk becomes a saved artifact before authoring widens: "the next
deciding walks become artifacts, not things we reconstruct from console archaeology."

**The method (`70086a72`), as the owner ratified it.** A new command, `livesession-window` on the host and
`livesession-selftest` over the mock, runs LIVE-INPUT-0's loop unchanged. The session hands every appended event to a
sink, and the sink is an append-only journal. It lives at `build/sessions/<run_id>/journal.vsj` (`VERDANDI_SESSIONS`
overrides the root, which is gitignored). The journal holds one text record per line, `R <length> <sha256> <payload>`:
a header, then one record per event, each flushed to the disk before it is counted. Esc, or a closed window, ends the
session; it is not in itself "saved". The session is then written in the workshop's own session-walk format to a
temporary file, flushed, and moved over `session.json` in one step: `MoveFileEx` with `MOVEFILE_REPLACE_EXISTING |
MOVEFILE_WRITE_THROUGH` on Windows, and a rename and a directory flush elsewhere. The file carries a live block (the
run, the renderer identity, the lineage, the journal's count and hash, how the session ended, and the keyboard-focus
observation) and a seal, the sha256 of the bytes before it. The shell then reads the file back from the disk and
verifies it: the seal, then a replay through the shell's SESSION-WALK machinery to every witness, camera, content and
head of the live session. Only then does the run say saved and exit 0. A seal that cannot be written, or does not
verify, is a refusal. The renderer identity is the sha256 of the render sources the shell was built from:
`kernel/mantle.rs`, `formats.rs`, `fast.rs`, `hud.rs` and `shell/present.rs`, with line endings taken as the repository
keeps them, so a CRLF checkout names the same renderer.

Loading (`--resume`) goes in the owner's order. It verifies integrity first: the seal, or each journal record's length
and checksum (a torn final record is dropped, any other bad record refuses), the base files' W and M, the chain's own
fold, and the lineage. It then compares the renderer identity, replays, compares witnesses and classifies. Same
identity and all reproduced: LOAD. Same identity and a divergence: TAMPERED. A different identity and all reproduced:
LOAD, noted as a different renderer. A different identity and a *frame* witness diverging: DIFFERENT-RENDERER. One
refinement is written into the method: a divergence no renderer can explain (an edit's content, a move's camera) is
TAMPERED under any identity, because blaming it on the renderer would be a false attribution. A continued session is
sealed as a new file whose log begins with its parent's events. The parent's head therefore lies on the child's own
chain; the lineage names that head, its event count and the parent's bytes, and cannot merely claim a parent. The
parent file is never modified. The keyboard-focus observation (the foreground request's result, whether the window
held the foreground at the start, and how many compositions did and did not have it) is recorded, never ruled on.
`verify/livesession.py` turns a saved session into a committed record: `shell/attest/livesession-<host>-<head>.json`,
a RECORD-0 copy that shell playback and the workshop both replay. LIVE-INPUT-0's own command still writes nothing.

**Rows.** `livesession-preregistered`: the method is locked, and the shell's constants, the five identity sources (in
the shell and in the sealer) and the seal key are the registered ones. `livesession-save`: script A runs to Esc and is
saved. The journal is a header and one checksummed record per saved event. The seal recomputes, the renderer identity
is the one recomputed from the checkout, and the workshop's `sessionwalk verify` passes on the saved file itself. PLANTS:
an unwritable seal, a file corrupted between its write and its verification, and a sealed, self-consistent file that is
not the live session (added after a mutation that skipped the comparison went unseen) each refuse (logged, ledgered) and
never say saved. `livesession-resume`: continuing the saved session writes a new file whose first 23 events are the parent's,
whose lineage lies on its own chain, whose three new events are the expected ones, and which the workshop verifies; the
parent's bytes are unchanged. `livesession-recover`: a run that dies after five journaled events leaves a torn final
record, no saved session and no ledger line. Resuming from its journal drops the torn record and saves the five events
with one more, naming the journal as the lineage. A bad middle record, a missing header and a record head that does not
fold each refuse. `livesession-classify` checks the loader against real shells built from changed sources:
- a consistent frame forgery under the same shell is TAMPERED;
- CRLF line endings name the same renderer (LOAD);
- a comment-only render change loads as LOAD with a different renderer, and its continuation names both identities;
- a digest-changing render source is DIFFERENT-RENDERER;
- a forged edit witness is TAMPERED under a different identity;
- an altered seal, a changed base and an off-chain lineage refuse before any replay.

`livesession-sealer` seals the gate's saved session and replays the copy in shell playback and the workshop; five
malformed sessions are refused. `livesession-fence` covers the invariants:
- each journal record is flushed before it is counted, and the journal only appends;
- the saved file goes through a flushed temporary and the atomic replace with both flags, and is verified from the
  disk before the run says saved and ends 0;
- every refusal ends the ledger;
- the loader runs in the registered order, with only a frame renderable;
- the reader opens no file, and the sink sees each event after it is appended;
- the host window loads first, observes the focus without ruling on it and writes nothing;
- `build/sessions/` is gitignored;
- a windowless build refuses the command.

`liveinput-fence` now bounds its playback section at the next appended section (LIVE-SESSION-0's reader), which its own
fence judges. 26 mutations were each caught. The first pass missed three, each now caught by a sharper check: a bad
journal record just before the torn tail, the seal-stale plant, and the fence pinning the lineage condition.

**The first saved host walk (DANIELDILLBERG).** After 0072 was applied, the gate read 164 rows (rowset
`ab16618fd6fadf04`, the same as in the container). The window shell was built with `--cfg shell_window` and started
with `livesession-window`. The window said it held the keyboard at the start. The owner then walked freely, not
script A, so no head had been stated beforehand and none is compared. There were 48 presses:
- 37 events: 33 moves (11 of them blocked) and 4 edits;
- the cell ahead at (29,28) closed, opened and closed again, and (25,29) opened;
- 11 unbound keys ignored;
- no refused edit.

The loop rendered and presented 5,873 compositions live, and all 99 screen readbacks were exact. The session ended
`closed`: the window was closed rather than Esc pressed, which the method treats as the same end. The seal and the
verification ran all the same, and the shell printed that `build/sessions/1a0e9bbbb92-82c0/session.json` was saved and
verified, with 37 events and head `aa850e786b6f0d33…627dea`.

The saved file (sha256 `1e2e9f135af39ac0…865b`, 6,205 bytes) and its journal (sha256 `b1fa7c80…ace6e`, 38 records)
were copied from the host unchanged and checked here, on another machine, without the host:
- its seal, base, fold and counts check;
- the journal's hash is the one its live block names;
- the workshop's own `sessionwalk verify` passes on the file itself, to head `aa850e786b6f…`;
- shell playback replays it to the same head and final camera 25,27,N;
- the renderer identity it names (`629ae5c7…e3c9`) is the one this checkout's sources give, so the Windows host and the
  container name the same renderer;
- resuming it loads as LOAD with its 37 events, and so does resuming from its journal alone.

The focus observation says the foreground request succeeded, the window held the foreground at the start, and it held
it for 5,874 of 5,875 message pumps, losing it only at the closing pump. That is recorded and explains nothing about
LIVE-INPUT-0's first run. The owner sealed the committed copy with `verify/livesession.py`:
`shell/attest/livesession-DANIELDILLBERG-aa850e786b6f.json` (chain `ef841693…`). Its record names the saved file's
sha256 above, cites LIVE-SESSION-0 (`70086a72`), and replays here in shell playback and the workshop to head
`aa850e786b6f…`.

**The resumed host walk (DANIELDILLBERG).** `livesession-window --resume` on the saved file loaded it as LOAD (37
events, head `aa850e786b6f…`, the same renderer), and the owner walked on. There were 255 presses:
- 197 new events, 195 moves (7 of them blocked) and 2 edits, closing (25,25) and (27,26);
- 51 auto-repeats counted and never bound, the first host evidence that holding a key does not walk;
- 6 unbound keys ignored;
- no refused edit.

The walk went west along row 26 to (4,26), north up column 5 to (5,6), then east and south through the rooms and
corridors back to (25,27). The loop rendered and presented 5,557 compositions live, and all 217 screen readbacks were
exact. This time the session ended by Esc, the registered path, and was saved and verified as a new file,
`build/sessions/1a0e9cfc4f4-ac94/session.json` (sha256 `16b011cf…a3a3`), with 234 events and head
`5290c848217d4b95…6632d`. The foreground request succeeded again, and the window held the foreground for 5,558 of 5,559
pumps.

Checked here from the unchanged bytes:
- **The child file:** its seal and counts check; the workshop's `sessionwalk verify` and shell playback both reach
  head `5290c848217d…` and final camera 25,27,S; its journal (235 records, sha256 `7145a5f3…8978`) is the one its live
  block names, and its header carries the lineage.
- **The lineage:** the child's first 37 events are the parent's, over the same base; it names the parent's head
  `aa850e786b6f…`, its 37 events and the parent's bytes (`1e2e9f13…`); the parent's head lies on the child's own chain
  at event 37; and the parent file on the host is byte-for-byte unchanged.
- **Resume here:** resuming the child loads as LOAD with its 234 events.

**Grade.** DECLARED: the method. ESTABLISHED (gate): saving, resuming, recovery from a crashed journal, the loader's
classification against real changed shells, the sealer, and the fence. MEASURED (host, two saved walks): a live walk,
and its continuation into a new file, each saved by the shell and verified there before it counted as saved. Each
verifies unchanged on another machine through the workshop's own `sessionwalk`, shell playback and the loader, with the
same renderer identity on both hosts. The continuation's lineage lies on its own chain, and its parent was untouched.
The walks are artifacts, not transcripts. NOT_MEASURED (host): recovery from a crashed run, and a refused edit.

**does_not_show.** Durability beyond the file system's promise: a disk that acknowledges a flush it did not perform is
outside the claim. The seal is a checksum, not a signature: forgery is caught by replay and by the committed RECORD-0
copy. The renderer identity names sources, not pixels. A crashed run keeps only what was flushed. The focus observation
explains nothing. New authoring vocabulary, a SendInput-driven walk and an independent screen witness are not part of
this rung.

**Falsifier.** `livesession-save` goes red if a run says saved without a verified file, or a plant stops refusing.
`livesession-resume` goes red if the parent changes or the lineage leaves the child's chain. `livesession-recover` goes
red if a torn tail refuses or a bad middle record is dropped. `livesession-classify` goes red if an identity mismatch
is treated as corruption, or a content divergence is blamed on the renderer. `livesession-fence` goes red if durability
is claimed before it is earned.

## LIVE-AUTHOR-0 — the thing authored is what the next frame renders: tile classes painted live, commit-only (preregistered and built; painted live on the host, saved, and resumed there with the painting intact)

**Why.** LIVE-INPUT-0 showed that cell edits reach the session and the screen, and LIVE-SESSION-0 made the session
durable. LIVE-AUTHOR-0 is the owner's last authoring-primitive slice. It adds a second kind of authority, M (the
materials), through the same pathway, then stops adding bespoke input cases. From here on, new vocabulary joins one live
editor rather than a new pathway.

**The method (`9a3e4521`), as the owner ratified it.** One live editor command, `live-window` on the host and
`live-selftest` over the mock, runs LIVE-SESSION-0's durable loop (journal, seal, verification, `--resume`) under the
authoring binding. That is LIVE-INPUT-0's keys unchanged, plus 1, 2, 3, 4 and 5 for the tile classes wall0, wall1,
wall2, wall3 and floor. A class key appends one edit, `tile:CLASS,R,G,B`, a solid fill of the whole class. Its colour
is the entry after the class's current colour in a registered 8-colour palette (umber, stone, brick, slate, moss, sand,
plum, chalk), or the palette's first entry if the class is textured. The current colour is read from the session's own
M, so the same key over the same M always gives the same edit. The edit is a SESSION-WALK event like a cell edit: the
session applies it, its witness is the new content, it folds into the head, and it is journaled and sealed. The loader
now replays tile edits as it replays cell edits.

It is commit-only. There is no preview and no provisional colour, and the authoring module holds no state; the loop
changes M only by appending the edit. The frame witness is the index frame, which a colour does not move. So the
picture is witnessed per state by the reference composite's sha256 (the pixels), and the loop now records it for every
state. The camera control condition is that a camera-only event changes the pixels and the frame witness while W and M
stay unchanged. Its converse is recorded too: a tile edit changes M, leaves W and the frame witness unchanged, and
changes the pixels exactly when the class is on screen. `liveinput-*` and `livesession-*` keep their own bindings, so
the class keys stay unbound there.

One witness was added during the build. A reference-only check has a blind spot: a loop that recorded each new state's
reference but kept presenting the previous state's frame would pass it, because its byte check compares the stale frame
with the stale reference. A mutation showed exactly that. So the loop also records, at each state's first composition,
the sha256 of the frame it actually handed to the call, and the gate requires that to be the state's own reference.

**Rows.** `liveauthor-preregistered`: the method is locked, and the shell's palette, binding, next-colour rule and tile
class order are the registered ones.

`liveauthor-binding`: script C from 28,28,N becomes exactly its registered outcomes at its registered compositions. It
paints the floor while the floor is off screen, turns west, cycles the floor through all 8 colours and back to the
first, paints each wall class, turns back, opens a cell and walks through it, and ends with Esc. That is 18 presses and
13 tile edits in palette order. The class keys stay unbound in `liveinput-selftest`.

`liveauthor-authority`: every tile edit changes M and leaves W and the frame witness unchanged. Its pixels change
exactly where script C registers the class on screen. The registration is taken from the renderer's own output: the
floor is off screen facing north and wall1 facing west, and those two edits are the off-screen controls, whose pixels
stay the same. Every turn changes the pixels and the frame witness with W and M unchanged. The tile edits alone leave
the level's bytes unchanged. Every state's presented frame is the one rendered from its own authority. The workshop's
`sessionwalk` replays the saved log to its head, and the content recomputed from the log is the saved one.

`liveauthor-persist`: every tile edit was journaled as it was made, one record per saved event. Resuming script C's
saved session loads as LOAD, and its first presented picture is its parent's last (the same pixels and frame witness). The next floor edit takes the palette's next colour and is sealed into a child
with lineage, which the workshop verifies; the parent is unchanged.

`liveauthor-fence`: the authoring module holds no colour, tile or preview state and makes no edit. The Tile arm reads the
session's colour, appends `push_edit_tile`, then renders the resulting state. The session's tile edit follows the cell
edit's own path (apply, content, fold, append, hand to the sink). The live command runs LIVE-SESSION-0's `go_with` under
the authoring binding, while LIVE-INPUT-0's `run` and LIVE-SESSION-0's `go` keep their own. The host window is
LIVE-SESSION-0's window under the binding, and a windowless build refuses it.

`liveinput-fence` and `livesession-fence` are re-pinned on purpose: the loop, the runner and the window now take their
binding as a parameter. 15 mutations were each caught. The first pass missed two, now caught: a stale presented frame
(by the presented-frame witness) and a tile edit not journaled (by the journal check in `liveauthor-persist`).

**The live editor on the host (DANIELDILLBERG).** After 0075 was applied, the gate read 169 rows (rowset
`2d23d28286297bae`, the same as in the container), and `live-window` was built and run twice.
- **First run:** one turn (A), then Esc. It was saved and verified as `build/sessions/1a0ea070209-b500/session.json`
  (1 event, head `8759c67dece9…`).
- **Second run:** `--resume` on that file loaded it as LOAD, and the walk went on. There were 104 presses: 95 new
  events (93 moves, 4 of them blocked, and 2 edits), 5 auto-repeats ignored and 3 unbound keys ignored. The walk went
  east to row 26's end, north up column 43 to (43,15), through the north-east rooms and back down to (43,23). The two
  edits closed the cell ahead at (43,24) and opened it again, so the final content is the base content (`390109b5…`)
  again, exactly. The loop presented 1,992 compositions, all 101 screen readbacks were exact, and the session ended by
  Esc. It was saved and verified as `build/sessions/1a0ea11ce49-8208/session.json` (sha256 `f63024e3…15e4`, 96 events,
  head `ace4bcd59cc7…`).

Both files verify unchanged here in the workshop's `sessionwalk`. The second verifies in shell playback too, and its
seal, journal (97 records, sha256 `dc8380ea…ca84`) and lineage check. Its lineage names the first file's head, its one
event and its bytes, and lies on its own chain, and the renderer identity is the same on both hosts. The window held
the foreground for 1,993 of 1,994 pumps.

No class key (1–5) was pressed in either run. Those two runs measured the live editor as the durable, resumable loop
under the authoring binding, but not the painting, which the next run did.

**The painting walk on the host.** After 0076 was applied, `live-window` was run once more, as a new session from
28,28,N.
- **The walk:** 28 moves, none blocked. It went west along row 28 to (23,28), north to (23,26), then west along row 26
  to (7,26), facing west.
- **The painting:** 30 class-key presses. Two were 6, which is unbound and was ignored. The other 28 were tile edits
  across all five classes, each the palette's next colour for its class. The floor went through all 8 colours, umber to
  chalk. Wall1 and wall3 went umber to sand (6 each), and wall0 and wall2 went umber to slate (4 each).
- **The run:** 59 presses, no auto-repeats, 56 events (28 moves, 28 edits, none refused), ended by Esc. The loop
  presented 1,642 compositions, and all 62 screen readbacks were exact. The window held the foreground for 1,643 of
  1,644 pumps.
- **Saved:** as `build/sessions/1a0ea26c927-9cb4/session.json` (56 events, head `dd874eff3a69…`, final content
  `0461485a…`), saved and verified there. It was sealed by `verify/livesession.py` as
  `shell/attest/livesession-DANIELDILLBERG-dd874eff3a69.json` and committed (`6481c5e`).

The session was checked here from its staged bytes.
- **The file:** its seal, base and fold check. Its journal (57 records, sha256 `986fa542…86d7`) holds one record per
  saved event, and each equals the saved event. The renderer identity is the same on both hosts (`629ae5c7…`). The
  workshop's `sessionwalk` verifies both the saved file and the sealed record, and shell playback replays the record to
  the same head. The record's `saved_sha256` is the saved file's.
- **The colours:** every one of the 28 edits is the palette's next colour for its class, read from the M the events
  before it left. Each class's first edit took umber, because every class started textured.
- **The authority:** the gate's Python twin applied the 28 edits to the base bytes. The level's bytes (W) stayed
  unchanged through all of them. After each edit, the content it computes is that edit's witness, and the last is the
  saved final content.
- **The replay:** the same 59 presses, typed as a key script into `live-selftest` here, reproduce the session: the same
  56 events, head and final content. In that replay only wall3 and the floor are on screen at (7,26) facing west.
  14 of the 28 edits (6 to wall3, 8 to the floor) changed the picture. The other 14 (wall0, wall1, wall2) changed M
  and left the picture unchanged. No edit moved the frame witness.
- **The resume:** resuming the staged file here loads it as LOAD with the painted content, and a continuation (two
  turns, then Esc) was saved and verified with lineage. The host's own resume is below.

**The painted session resumed on the host.** After 0077 was applied, `live-window --resume` was run on the painted
session's file.
- **The load:** it loaded as LOAD (56 events, head `dd874eff3a69…`), with the window holding the keyboard from the start.
- **The walk:** two turns to face east, 15 steps east along row 26 to (22,26), and a turn to face south. Then two
  class keys: wall3 went from sand to plum and wall2 from slate to moss, each the palette's next colour.
- **The run:** 21 presses, 20 new events (18 moves, none blocked, and 2 edits), ended by Esc. The loop presented 727
  compositions, and all 26 screen readbacks were exact. The window held the foreground for 728 of 729 pumps.
- **Saved:** as `build/sessions/1a0ea782d9e-b20c/session.json` (sha256 `196bc7e7…80da`, 76 events, head
  `eaf27cf3fc0c…`, final content `61f180d1…`), saved and verified there. It was sealed as
  `shell/attest/livesession-DANIELDILLBERG-eaf27cf3fc0c.json` and committed (`5539d70`).

Here, from the staged bytes:
- **The file:** the seal, base, fold, journal (77 records, sha256 `3dd58cd4…ae66`) and lineage check. The lineage
  names the painted session's head, its 56 events and its bytes (the staged parent's sha256). The child's log begins
  with the parent's 56 events unchanged.
- **The replay:** the workshop's `sessionwalk` verifies the saved file and the sealed record, and shell playback replays
  the record to the same head. The renderer identity is the same as the one the session was made with. The Python twin
  keeps the level's bytes unchanged through all 30 edits, and its final content is the saved one.
- **The picture:** the same 21 presses, typed as a script into `live-selftest --resume` over the painting walk's file,
  reach the same head. In that replay the resumed session's first picture is the painting walk's last (the same pixels
  and frame witness), and it is the frame the loop presented. At (22,26) facing south, the wall2 edit changed the
  picture, and the wall3 edit changed M with wall3 off screen.

**Grade.** DECLARED: the method. ESTABLISHED (gate): the binding and the palette order, the authority checks (tile edits,
the off-screen controls, the camera control condition, the workshop's replay), persistence through save and resume, and
the fence. MEASURED (host), three things. The live editor command. The painting: class keys pressed live on the host
made 28 tile edits, each the palette's next colour, saved and verified there and here, with the level's bytes unchanged.
Its persistence: the painted session was resumed on the host as LOAD, walked and painted further, and saved as a
verified child whose lineage names it. Every screen readback in all four host runs was exact. A crash recovered on the
host is still LIVE-SESSION-0's open item.

**does_not_show.** Per-cell materials, or a way back to a textured tile: an edit is a solid fill of a whole class.
Colours outside the palette. Whether a class is on screen by any rule: it is registered per scripted state from the
renderer's output. For the host's walks, which edits changed the picture and that the resumed first picture is the
painted one: both are registered from the replay here, because the window writes no pixel witnesses. On the host, each
readback matched the reference rendered from the session's own authority. What reached the screen between readbacks.
Continuous movement, a cursor, a preview. Timing.

**Falsifier.** `liveauthor-binding` goes red if a class key or a colour is wrong, or the class keys leak into
LIVE-INPUT-0. `liveauthor-authority` goes red if a tile edit touches W or the frame witness, misses M, changes the
pixels of an off-screen class or not those of an on-screen one, or if a turn touches W or M or leaves the pixels alone.
`liveauthor-persist` goes red if the resumed picture is not the parent's last. `liveauthor-fence` goes red if a colour
is held, previewed or applied outside the session.

## HOLD-WALK-0 — holding a key walks the live editor; the world stays discrete (preregistered and built; a held walk measured on the host; not the free movement the owner wants)

**Why.** The route's next step after LIVE-AUTHOR-0 was free continuous movement, as vocabulary on the one live editor.
The frozen renderer draws the eye only at a cell centre facing N, E, S or W, and Urðr's frozen game boundary keeps
in-between positions out of canonical state. So on this route, free movement is held keys over the same discrete
world. The owner named the rung HOLD-WALK-0 to keep the claim precise: the input is continuous, the world state is not.

**The method (`c03260a2`), as the owner ratified it.** The live editor (`live-window`, `live-selftest`) binds a fresh
press exactly as LIVE-AUTHOR-0 does. The held keys are W, A, S, D and the four arrows: the steps and the quarter turns.
A held key's auto-repeat (the repeat bit of WM_KEYDOWN) is bound as that key's move and appends an ordinary move event,
the same event a press makes. Keyboard repeat is the speed source, capped at one admitted repeat per composition:

- Among the presses one composition drains, the first repeat of a held key walks.
- Every later repeat in that composition is coalesced: counted and traced, never an event, never silently dropped.
- A fresh press is never coalesced.
- A repeat of any other key (Q, E, Space, 1–5, Esc) is ignored as before, so holding Space or a class key edits once.
- A held step into rock appends a blocked move for each admitted repeat, as pressing does.

The shell keeps no clock, reads no key-up and carries no key state between compositions: the admitted flag lives inside
one composition. When the key is released its repeats stop, so no event is made without a press. Free look is a held
quarter turn. LIVE-INPUT-0's and LIVE-SESSION-0's commands pass no held set, so their repeats still bind nothing. The live
editor's console adds one line, `liveinput held repeats R walked W coalesced C ignored I`. The mock's key scripts gained
groups: presses joined by `/` arrive in one pump, so the gate can deliver several repeats to one composition.

**Rows.** `holdwalk-preregistered`: the method is locked, and the shell's held set is the registered one. It is exactly
the keys LIVE-INPUT-0 binds to a step or a quarter turn, with no strafe and no edit key, and the key code alone decides.

`holdwalk-binding`: script H from 28,28,N, 24 presses in 19 groups, becomes exactly its registered outcomes at its
registered compositions. It walks west on a held W, with one group of three repeats (one walked, two coalesced). It
paints the floor and holds 5 (painted once), and holds Q (ignored). It turns south, steps, and holds W into rock (both
blocked moves). It holds D to look around (a group of two: one walked, one coalesced). It walks north with a held W and a
fresh W in one group (both events), then a held W and a held A in one group (one walked, one coalesced). It closes the
cell ahead with Space and holds it (one edit), holds W into the closed cell (blocked), and ends with Esc. That is 16
repeats (9 walked, 4 coalesced, 3 ignored) and 16 events. In `liveinput-selftest` and `livesession-selftest`, a held
key's repeats bind nothing.

`holdwalk-coalesce`: in script H's trace, no composition admits more than one repeat, every coalesced press follows its
composition's admitted repeat, and no fresh press is coalesced. The repeats are exactly walked + coalesced + ignored, and
every saved event is a traced press's.

`holdwalk-equivalence`: the same walk pressed (each walked repeat typed as a fresh press, the coalesced and ignored
repeats left out: 17 presses) saves session data byte-identical to the held walk's, with the same 16 events and head.
The workshop's `sessionwalk` verifies both. Holding a key adds nothing to the saved world.

`holdwalk-fence`: the held-set module holds no state and reads no clock. The admitted flag is declared inside each
composition, and the repeat branch walks only the first held repeat and counts the rest. LIVE-INPUT-0's run and
LIVE-SESSION-0's go and window pass no held set, and the live editor (selftest and window) passes HOLD-WALK-0's. The
window still reads only WM_KEYDOWN and its repeat bit: no key-up, no key state.

`liveinput-fence`, `livesession-fence` and `liveauthor-fence` are re-pinned on purpose: the loop, the runner and the
window now take a held set as a parameter, and each pins that its own command passes none (the live editor passes
HOLD-WALK-0's). 14 planted mutations were each caught: no coalescing; a coalesced or a walked repeat not counted; the
admitted flag carried across compositions; Space or Q in the held set; LIVE-INPUT-0 or LIVE-SESSION-0 binding repeats; a
fresh press coalesced; a stateful held-set module; a clock in the loop; a key-up read; an extra move on a walked repeat;
the mock's groups split.

**On the host (DANIELDILLBERG).** After 0079 was applied, the gate read 174 rows with none failing, including the five
`holdwalk-*` rows (rowset `2e986bf1e40bfc4b`, the same as in the container), and the window build was rebuilt. The held
walk did not run on the first attempt: it left no run-ledger line and no session folder, so it never reached the point
where a run opens its journal.

**The held walk on the host.** After 0080 was applied, `live-window --resume` was run on the painted session's child
(`build/sessions/1a0ea782d9e-b20c/session.json`).
- **The load:** it loaded as LOAD (76 events, head `eaf27cf3fc0c…`), with the window holding the keyboard from the start.
- **The walk:** a turn to face east, then W held along row 26 from (22,26) to (35,26); two turns, W held back west to
  (23,26); two turns, W held east to (33,26); two turns to face west.
- **The run:** 43 presses and 42 events, all moves, none blocked. Of the 31 auto-repeats, all 31 walked; none was
  coalesced or ignored, so at this host's repeat rate each repeat arrived in a composition of its own. It ended by Esc.
  The loop presented 839 compositions, all 48 screen readbacks were exact, and the window held the foreground for 840
  of 841 pumps. The console reported `liveinput held repeats 31 walked 31 coalesced 0 ignored 0`.
- **Saved:** as `build/sessions/1a0ef023794-b638/session.json` (sha256 `01d5d255…03f8`, 118 events, head
  `47ae5de3c73a…`), saved and verified there.

Here, from the staged bytes:
- **The file:** the seal, base, fold, journal (119 records, sha256 `817bd21c…6552`) and lineage check. The lineage names
  the parent's head, its 76 events and its bytes, and the child's log begins with them. The workshop's `sessionwalk`
  verifies the file, the renderer identity is the same, and the content is the parent's (no edits).
- **The equivalence:** the same 43 presses, typed as a key script into `live-selftest --resume` over the parent (each
  repeat marked, one per composition), reach the same head. Typed with every press fresh, they reach the same head too:
  the held walk saved exactly what pressing would have.

**The owner's verdict.** After walking it, the owner judged that held keys over the grid are not the free movement he
wants on this route. HOLD-WALK-0 stands as built and measured; what the route's free-movement item becomes is open.

**Grade.** DECLARED: the method. ESTABLISHED (gate, in the container and on the host): the held set; one admitted repeat per composition, with the rest
counted as coalesced; fresh presses never coalesced; a held walk saving the same data as the same walk pressed;
LIVE-INPUT-0 and LIVE-SESSION-0 unchanged; the fence. MEASURED (host): a held walk in the window. 31 held repeats each
walked, saved and verified there and here, reaching the head the same presses reach when pressed, every readback exact.
NOT_MEASURED (host): coalescing, since no repeat arrived in a composition that had already admitted one.

**does_not_show.** Any position between cells, or any angle between the four facings: the world is as discrete as
before. A walking speed or any timing: the speed is the keyboard's repeat rate capped by the loop, and only counts are
recorded. What Windows does with repeats before they reach the queue (the message's own repeat count is not read). How
long a key was held. Mouse-look, a cadence.

**Falsifier.** `holdwalk-binding` goes red if a press's outcome, a count or a saved event differs from script H's
registration, or if LIVE-INPUT-0 or LIVE-SESSION-0 binds a repeat. `holdwalk-coalesce` goes red if a composition admits
two repeats, a fresh press is coalesced, a coalesced repeat goes uncounted, or an event appears without a press.
`holdwalk-equivalence` goes red if holding a key changes the saved data. `holdwalk-fence` goes red if a clock, a key-up
or a key state enters.

## BEARING-0 — the bearing camera of urdr-oracle-2 carried, its reference kernel placed (preregistered and built; the gate passes on the host)

**Why.** After HOLD-WALK-0 the owner ruled what free movement means here: shooter-style mouse-look, taken in rungs. The
first rung is the camera alone: any heading, the eye still at a cell centre. Outside the four cardinal cameras no frozen
oracle existed to hold a renderer to, so the owner ruled that the turning camera be earned in Urðr and re-frozen there,
not invented here. Urðr did that as VIEW-YAW-0: its D26 preregistration, then the `bearing` module (URDRBRG1) admitted
against it. There, a heading is an integer id in [0, 360000), millidegrees clockwise from north, naming one primitive
Pythagorean triple (A, B, C), so the renderer consumes exact rational directions and never an angle. The four cardinals
are anchors that reproduce `vista`'s and `mantle`'s frames byte for byte, and a std-only Rust placement reproduces all
104 corpus witnesses, on the gate's Linux host and on the owner's Windows host. The record `studio-oracle-2.json` froze
it for consumers, and the owner cut the tag `urdr-oracle-2` (`ad6d55fe`) on 2026-09-30.

**The court of 2026-10-01 (the owner's rulings).**

- **The route.** BEARING-0 (the reference) → BEARING-FAST-0 (the production candidate) → MOUSE-LOOK-0 with SIM-TICK-0 →
  the presentation and latency measurement. The reference renderer is the correctness court; a fast renderer is a
  production candidate, held byte for byte to the reference over the bearing corpus and an adversarial camera set, and
  never becomes the oracle. That is GAUNTLET-1's lesson, applied again. Mouse-look does not drive a renderer slower than
  the display: the reference measured here is about twice the facing kernel's single-thread time, below a 60 Hz cadence
  on the owner's host by estimate.
- **The optimization order for BEARING-FAST-0.** (A) single-thread arithmetic and layout: hoist the camera's invariant
  terms and turn per-pixel work into per-row or per-column recurrences where exactness permits, the floor DDA's lesson;
  (B) memory and layout, measured rather than guessed; (C) parallel emission; (D) a persistent worker pool; then (E)
  mouse-look as a thin input producer. The first target is to beat the measured display interval with margin, then to
  measure the production render and present path. 144 Hz is not the first target.
- **What a competitive claim needs.** Simulation and input, camera command, production render, frame ready, present,
  display refresh and photon are separate segments. The renderer establishes one of them, and the present here is
  refresh-coupled, so frame rate alone establishes no competitive latency; input to photon needs a physical measurement.
- **W/A/S/D under a free heading.** W steps one cell toward the cardinal nearest the heading. Each cardinal owns the
  90° sector centred on it (±45°). At the exact boundary ids (45000 + 90000n) the clockwise cardinal wins, so the rule
  is a function of the id: forward = ((k + 45000) div 90000) mod 4, with 0 N, 1 E, 2 S and 3 W. S is its opposite, A and
  D the cardinals 90° left and right of it. W/A/S/D never change the heading: the mouse changes the heading, the keys
  read it, and the existing MOVE authority executes the cardinal step. Diagonal steps would be a new movement law,
  with corner-cutting, distance and collision questions of their own, so they are not on this route.
- **SIM-TICK-0.** 64 Hz (15,625 µs per tick). Each tick saves one command: the integer heading delta summed from the
  mouse during the tick, plus the key presses. Replay runs the ticks exactly.
- **Sensitivity.** Heading delta = mouse counts × multiplier × step, where the step is 88 ids (0.088°) coarse or 1 id
  fine, toggled, and the multiplier is a positive integer, adjustable and saved in the session. The mouse-to-heading
  path is integer from end to end. The session saves the resulting integer heading delta, or the exact inputs with
  the registered configuration, never raw counts as the semantic result and never a float.
- **The live check (carried from the first FPS court).** A live frame is rendered once. While live, preregistered
  sampled checks are run by an independent path, and every session is certified by exhaustive replay at save and at
  the gate. Sampling never certifies a session.

MOUSE-LOOK-0 and SIM-TICK-0 register these rulings in their own preregistrations when they are seated.

**The method (`de19660f`).** The record and the octant are carried verbatim from the tag as
`oracle/urdr-oracle-2.json` and `oracle/bearing_octant.txt`; urdr-oracle-1's carry is untouched, and oracle-2 names it
by its sha256. The camera is C = (cell_x, cell_z, heading id). The id is authoritative, read only in canonical decimal
and never normalized. Its triple is the vocabulary's: `kernel/vocab.rs` compiles the carried octant in and checks it
against the record's sha256 before reading any triple, so a file that does not match refuses and is never regenerated.
It expands the octant by the record's exact symmetries and composes the bearing camera into the oracle's `URDRBRGI`
scene. `kernel/bearing.rs` is Urðr's `bearing_rs/bearing.rs` at the tag. Only visibility and shape changed: its core is
the source's text with `pub` added, the scene parser refuses typed (BEARING-REFUSE) instead of exiting, the command line
moved to `kernel/main.rs` (`--at x,z,K`, `--bearing-table`, `--bearing-triple K`, apart from the facing path and
combining with none of its flags), and SHA-256 is mantle.rs's. It is the reference: never modified for performance, and
no live window uses it. The shell, `mantle.rs` and `fast.rs` are unchanged.

**Rows.**

- `bearing0-preregistered`: the method is locked.
- `oracle2-frozen`: the two files are the tag's bytes. The record extends the carried `urdr-oracle-1.json` by its
  sha256, its two views are scenes of `witnesses.json` on their own levels (seed, depth and cell agree), its anchor
  witness at W is urdr-oracle-1's three hashes, and its anchors are the cardinals.
- `oracle2-identity`: the checker is not the prover. From the record and the octant alone, with nothing of Urðr
  imported, the row recomputes by the record's own stated rules the table digest over all 360,000 ids, the largest
  hypotenuse (8,404,122,277), the 26 case hashes and URDRBRG1's identity. All equal the record's.
- `bearing-vocab`: the kernel's table digest over all 360,000 ids is the record's. Its triple at the four anchors and
  the thirteen adversarial ids is the expansion's and the record's. Ten malformed ids (out of range, signed,
  zero-padded, fractional, spaced, empty, hex) are each refused typed.
- `bearing-oracle`: the reference reproduces all 104 witnesses of urdr-oracle-2 bit for bit: 26 cases (13 adversarial
  ids from the witness and corridor views, hypotenuses up to 2^33) × 2 tile sets × the frame digest and the pixel
  sha256. Each selfcheck is OK, the tile sets of a case share one frame, and one case run twice in separate processes
  agrees.
- `bearing-anchors`: at C = 1 the reference is the facing kernel. Over the six corpus scenes in both tile sets, the
  reference's frame and pixels at each anchor equal the facing kernel's at that cardinal, computed live (48 pairs, 12
  of them the frozen pins). A reference with screen-right mirrored fails the anchor law at every scene.
- `bearing-selftest`: a reference that drops C from the depth (the frozen strip expression used verbatim) moves the
  frame digest of every one of the 52 non-anchor scenes and leaves the witness anchor at W untouched.
- `bearing-refuse`: an octant with one pair altered into another canonical pair, compiled in, is refused at load by its
  pin, with no table and no frame. The same binary's facing path still reproduces urdr-oracle-1. An eye on rock and
  five malformed bearing cameras are refused typed.
- `bearing-fence`: the reference's core, `pub` removed, hashes to the same span of the tag's source. Neither file reads a
  clock, spawns a thread, touches a file at run time or uses unsafe. The vocabulary's one include is the carried octant
  under the record's pin. No file of the shell or the workshop reaches either.

The 104 witnesses reproduced on the first full run. Twelve planted mutations were each caught:
- a sign flip in the mirror expansion;
- zero-padded ids accepted;
- the id range off by one;
- A and B swapped in the composed scene;
- the pin check skipped (caught only after the registered plant was made canonical: the first plant, a non-canonical
  pair, was refused by the parser's structure and did not test the pin);
- a floor term without C;
- a comment edited inside the reference's core;
- `--at` reading the identity tiles for the oriented set;
- one byte of the record changed;
- the shell naming the vocabulary;
- the shell naming `kernel/bearing.rs`;
- a clock in the vocabulary.

**On the host (DANIELDILLBERG).** The preregistration (0082) was applied and pushed alone first (`853970b`). The build
(0083) first refused to apply: 0081, HOLD-WALK-0's host documentation, had not been applied there, and 0083 was cut on
top of it. Applied in order, 0081 then 0083 landed. The first gate run there then read 182 of 183 rows passing:
`oracle2-frozen` refused with "the record extends another studio-oracle-1 than the one carried". The cause was the
host's working copy, not the carry. `oracle/urdr-oracle-1.json` had been checked out on 2026-09-23, three days before
`.gitattributes` set `eol=lf`, and git does not rewrite a checked-out file when the rule changes. So that one file stood
on the host with Windows line endings: 2,980 bytes against the repository's 2,890, the same content line for line.
`oracle-frozen` reads the record as JSON, so until now no row had hashed its bytes. Its sha256
`470d3ab2…`, pinned in `oracle/README.md`, was asserted but not enforced. `oracle2-frozen` is the first row to enforce
it, because urdr-oracle-2 names urdr-oracle-1 by that hash. The row was kept strict and the file was re-checked out
(deleted, then `git checkout`), and `git status` read clean. The gate then passed: 183 rows, none failing or skipped,
rowset `0dfa172e19a93f80`, the same as in the container. The nine BEARING-0 rows were green both times, so the 104
witnesses, the anchor law, the C law's plant and the fail-closed pin all hold on the owner's Windows host. It was
pushed (`853970b..ac22fd3`). No turned frame was shown in a window there: BEARING-0 drives none.

**Grade.** DECLARED: the method, and the court's rulings for the rungs after this one. ESTABLISHED (gate, in the
container and on the host): the carry, the identities recomputed from the record alone, the vocabulary over all 360,000 ids, the 104
witnesses, the anchor law and its mirror plant, the C law's plant, the fail-closed pin, the fence. NOT_MEASURED: any
speed. Off the gate here, the reference ran about twice the facing kernel's single-thread time; no record was sealed,
and the frame rate is BEARING-FAST-0's court. DECLARED, as in Urðr: the quarter-millidegree angle bound.

**does_not_show.** Speed, a frame rate or any latency. Any position between cells, pitch or eye height. The mouse, a
tick, any movement change, or any live window at a bearing. Agreement between the oracle's 26 cases beyond the port
being the source's arithmetic; the wider adversarial camera set is BEARING-FAST-0's to register. That every other
file in an older checkout matches its committed bytes: the line-ending gap was found for the one file a row now
hashes, and the rows that read the others parse them.

**Falsifier.** `bearing-oracle` goes red if one of the 104 witnesses differs. `bearing-anchors` goes red if an anchor
is not the facing kernel's frame and picture. `oracle2-identity` goes red if any digest the record states does not
follow from the record and the octant by its own rules. `bearing-refuse` goes red if the vocabulary is read after its
pin fails. `bearing-fence` goes red if the reference's core changes or a live path reaches it.

## BEARING-FAST-0 — the bearing camera made fast, held byte for byte to the reference (preregistered and built; measured on the host: tread C meets the target, the sweep exact)

**Why.** The reference bearing kernel is exact and slow: in the container it ran about twice the facing kernel's
single-thread time, so mouse-look waits for a fast path. The owner's court of 2026-10-01 ruled the shape. There is one
rung with its staircase inside, as GAUNTLET-1 was: A, exact stepping; B, memory layout; C, threads; D, persistent
workers, only if needed. Each tread goes reference-equivalent, then byte-identical, then benchmarked on the host, then
retained or rejected. The optimizing stops when the target is met, and a later tread is kept only by beating its
predecessor by a margin, so none is kept merely because it exists. The owner added: try to do better than the target.
The target is a production p99 of at most 6,667 µs, half the panel's 13,333 µs at 75 Hz. Every narrowing from 128 to
64 bits carries a written bound, and the gate also runs a build with overflow checks on.

**Where the time was.** Reading the reference: almost all of it was per-pixel 128-bit division. A floor pixel did six
(two for its cell, four for its texel), a wall pixel one, and 128-bit division is a runtime routine (`__divti3`), not
an instruction. The traversal is not the cost: profiled here, the reference's strips took about 0.1 ms of a frame.

**The method (`f0a9a57d`), registered before any fast code existed.** `kernel/bearingfast.rs` is a sibling of the
reference. It reuses the reference's traversal (`Scene::strips`) unchanged and replaces the index frame and the
picture.

- **The exact walker.** A quantity N(j) = N0 + j·s seen through floor(N·T/den) is carried as M = floor(N·T/den) and
  its remainder e. One step adds s·T split once into a quotient and a remainder, with one carry. M and e are set up
  once from N0 in 128 bits; every step after that is a few 64-bit adds.
- **Tread A.** Along a screen row the floor point moves by a fixed exact step per column, at any heading: the floor
  numerators step by −2·B·EYE_Y and +2·A·EYE_Y, because the ray is linear in the column. This is Lode's scanline floor
  casting, made exact. With T = Q the walker's M is the floor point in texel units, so the cell is M >> 8 and the
  texel M & 255, exactly the reference's div_euclid and texel. Down a wall column, v's numerator steps by 2·C·tn per
  row, one walker per column, clamped as the reference clamps. The index frame and the picture are written together,
  row by row, in address order; the reference fills them column by column.
- **Tread B.** The floor tile is read from the 8×8 blocked execution format LOCALITY-0 locked (`fast::blocked_floor`,
  once per scene).
- **Tread C.** Contiguous row bands run on scoped threads (PROD_THREADS = 8), over either layout (`ca`, `cb`). Each
  band seeds its own wall walkers at its first row, and the writes are disjoint.
- **Bounds.** The envelope (C < 2^33, tn < 2^14, td < 2^45) is checked per scene and per strip, and a scene outside it
  is refused (BEARING-FAST-REFUSE), never wrapped. The seven narrowings go through one checked `narrow`, because an
  `as` cast is not covered by overflow checks; each carries its bound.

**Rows.**

- `bearingfast-preregistered`: the method is locked.
- `bearingfast-court`: in kernel processes, all four treads (a, b, ca, cb) produce the reference's index frame and
  picture byte for byte at all 1,972 cameras. Those are the 52 oracle scenes, whose reference digests are also
  urdr-oracle-2's own, and the 1,920 registered frames: six corpus scenes × eight cells by the registered rule × forty
  headings (anchors ±1, diagonals ±1, anchors ±88, eight generic ids), with the list's digest pinned. The gate splits
  the list across processes for wall-clock only; every number reported is a function of the list.
- `bearingfast-threads`: tread C is the reference at T in {1, 2, 3, 7, 8, 16}, both layouts, over the 52 oracle
  scenes.
- `bearingfast-checked`: the kernel built with overflow checks on renders every tread at all 1,972 cameras without an
  overflow. Each camera hashes one tread in rotation, and that digest equals the reference's.
- `bearingfast-bounds`: there are exactly seven narrowings, each through `narrow` with its bound, and no other
  `as i64`. At the registered heading with the largest hypotenuse (id 1, C = 8,404,122,277) every tread is the
  reference. Beyond the envelope (a triple with C = 5·2^31) the reference renders and the fast path refuses.
- `bearingfast-fence`: the reference's core is still the tag's text, and mantle.rs and fast.rs are unchanged (both
  pinned). The fast path reads no clock, touches no file, uses no unsafe and starts threads only in tread C's one
  scope. No file of the shell or the workshop reaches it.

**First runs.** The full court passed on its first complete run: every tread equal at every camera. The checked build
did not pass on its first run. It stopped on a u8 overflow in a value the release build had wrapped silently: the
sky's band, computed for every row, including rows below the horizon where no sky pixel can be (a strip's top is at
most CY). The band is now formed only above the horizon. The release output was the same before and after, so only the
checked build could have shown it. Fourteen planted mutations were each caught:
- a walker carry off by one;
- a floor step's sign;
- the blocked index transposed;
- band rows dropped;
- wall walkers seeded at the strip's top instead of the band's;
- the edge ink dropped;
- the floor band off by one;
- the sky guard removed (caught only by the checked build);
- an unchecked narrowing;
- the envelope check removed;
- a comment edited in the reference's core;
- a clock in the fast path;
- the shell naming it;
- a registered heading changed.

**Off the gate, on the owner's host.**
- **The speed court** (`verify/bearingfast.py`, sealed as `kernel/attest/bearingfast-<host>.json`). Each tread runs in
  its own process, at four registered cameras, twice in mirrored order. Every process checks its tread against the
  reference before printing a number. A tread's score is its worst camera's p99 (the larger of its two runs). Then:
  A is promoted if below the reference at every camera; B is kept at ≤ 950‰ of A; C over the kept layout at ≤ 950‰ of
  the best so far. The production candidate is the last tread kept, and the target is a score ≤ 6,667 µs.
- **The sweep** (`verify/bearingsweep.py`, sealed as `kernel/attest/bearingsweep-<host>.json`). Every walkable cell of
  the five corpus levels at every whole degree (622,440 frames), the production candidate against the reference.

Container timings are engineering notes and decide nothing. Here, with two cores, tread A ran about 12–13 ms at p50
against the reference's 40 ms, and C about 8 ms.

**On the host (DANIELDILLBERG).** 0085 (the preregistration) was pushed alone first, then 0086. The gate read 189 rows
with none failing or skipped, rowset `af17db8ca2521498`, the same as in the container, so the court, the threads set,
the checked build, the bounds and the fence all hold on the owner's Windows host too.

- **The speed court** (`kernel/attest/bearingfast-DANIELDILLBERG.json`, chain `d23443e5`, rustc 1.96.1, `-O`).
  Worst-camera p99 of the whole render, each tread the larger of its two mirrored runs:

  | tread | witness:123457 | witness:45000 | corridor:300001 | pointblank:270088 | score |
  |---|---|---|---|---|---|
  | reference | 59,901 | 39,060 | 49,559 | 21,345 | **59,901** |
  | A (exact stepping) | 7,042 | 5,989 | 5,350 | 6,616 | **7,042** |
  | B (A + blocked floor) | 7,290 | 5,880 | 5,542 | 6,261 | **7,290** |
  | C over A (`ca`) | 3,692 | 3,380 | 3,326 | 3,716 | **3,716** |
  | C over B (`cb`) | 3,636 | 3,168 | 3,335 | 3,211 | **3,636** |

  The registered rule, applied in order:
  - **A is promoted.** It is below the reference at every camera, by between about 3× (pointblank) and 9× (corridor).
  - **B is not kept.** Its 7,290 µs is above 950‰ of A's (6,690 µs): the blocked floor did not pay single-threaded.
  - **C over A's layout is kept.** Its 3,716 µs is under 6,690.
  - **THE TARGET IS MET.** The production candidate is `ca`, eight row bands of exact stepping, at a worst-camera p99 of
    3,716 µs. That is under 6,667 µs, and 28% of the panel's 13,333 µs period.
  - **The staircase stops at C, and D's trigger does not fire.** A alone missed the target (7,042 > 6,667), so C was
    required.
  - **`cb` is not chosen.** Its score was 80 µs (2%) lower than `ca`'s, inside the margin, and C runs over the layout
    already kept. This is recorded, not acted on.
  - **Reference spread.** The reference's first process at witness:123457 read 59,901 µs against 36,306 µs on its
    mirrored run. The larger-of-two rule kept the higher number. The reference's score decides only A's promotion,
    which held at every camera by a wide margin.
- **The sweep** (`kernel/attest/bearingsweep-DANIELDILLBERG.json`, chain `9c67987e`, naming the speed court's record as
  the source of its tread). Every walkable cell of the five corpus levels at every whole degree: 622,440 frames,
  `ca` against the reference byte for byte (index frame and picture). **622,440 equal, 0 differing.** It ran 87
  minutes on 15 processes; that wall-clock is informational.

**The owner's ruling after the court.** With the target met, the optimizing stops: `ca` is the production candidate, and
MOUSE-LOOK-0 wires it into a live path, not before. D is not built. SIMD, structure-of-arrays, cache and GPU work are
candidate courts to be measured first, with no gain claimed. The next evidence is the interaction seam (SIM-TICK-0,
sensitivity, live mouse-look), then the presentation boundary (PRESENT-1). No scalar scorecard is kept, and outside
estimates are not this repository's claims. A formal-methods branch, if opened, starts with one theorem: the exact
walker produces the same pixel inputs as the reference kernel for every admissible row, camera and scene. The full
order is in [`docs/ROADMAP.md`](../docs/ROADMAP.md).

**Grade.** DECLARED: the method, the staircase rule, the target. ESTABLISHED (gate, in the container and on the host):
byte-identity of every tread at the court set and the threads set, no overflow in the checked build over the court set,
the bounds and the envelope, the fence. MEASURED (host): the speed court (A promoted, B not kept, `ca` kept, production
`ca` at a worst-camera p99 of 3,716 µs, the target met) and the sweep (`ca` equal to the reference at all 622,440
frames).

**does_not_show.** Any present, blit, window or input-to-photon time: the score is renderer time only, on this host, in
this build, at these four cameras. Agreement at cameras outside the court set, the threads set and the sweep beyond the exact
arithmetic the gate bounds and overflow-checks. Any live use: no window renders at a bearing until MOUSE-LOOK-0.

**Falsifier.** `bearingfast-court` goes red if any tread differs from the reference at any registered camera, or the
camera list changes. `bearingfast-checked` goes red on any overflow. `bearingfast-bounds` goes red if a narrowing
escapes `narrow`, or the fast path renders outside its envelope. `bearingfast-fence` goes red if the reference, mantle.rs
or fast.rs changes, or a clock, a file or a live path enters.

## SIM-TICK-0 — the mouse-look rules as integer law, windowless (preregistered and built; the gate passes on the host, and the window build walks there as before)

**Why.** BEARING-FAST-0 gave a renderer fast enough to turn, and nothing yet says what a turn is. The owner's court
of 2026-10-02 split the work in two and forbade combining it: SIM-TICK-0 locks the rules with no window, and
MOUSE-LOOK-0 then puts a real mouse on them. The boundary is the owner's: raw input → tick command → SESSION-WALK →
authority, with "no Win32 input, clock scheduling, or live window behavior" allowed to contaminate the rule proof. The
same court ruled that the look is vocabulary on the one live editor (the saved session gains one event), that a free
heading shows the picture alone for now, and that a saved session is certified by the reference renderer, in parallel,
before it counts as saved, with no second, uncertified session state.

**The rules (`dc1dddf2`), registered before the build.** They are integers end to end, in `shell/simtick.rs`, which
holds no clock, file, static, float or thread.

- **The tick.** 64 Hz, exactly 15,625 µs. An input stamped t microseconds after the run began belongs to tick
  t div 15625. A time is an integer the caller hands over; this rung has no clock.
- **One command per tick.** A tick's mouse reports are summed (signed horizontal counts) and applied once, as one look.
  Then the tick's key presses and sensitivity actions apply, in arrival order. A tick whose counts sum to zero makes no
  look, and an empty tick makes nothing. Only the sum decides: how the counts were split into reports, and when inside
  the tick they arrived, cannot matter.
- **The look.** delta = counts × multiplier × step. The multiplier is a whole number from 1 to 64, starting at 1. The
  step is 88 ids (coarse) or 1 id (fine), starting coarse. The look uses the two in force when the tick began, so a
  sensitivity action takes effect from the next tick. A tick whose counts leave ±(2³¹ − 1) has its look refused; its
  keys still apply.
- **The heading.** k′ = (k + delta) mod 360000, into [0, 360000).
- **The nearest cardinal.** ((k + 45000) div 90000) mod 4: N, E, S, W, each owning 90,000 ids, the tie at an exact
  45° boundary going clockwise. The owner's ruling said ±22.5° in its text and fixed the tie at the 45° boundaries;
  the registration records the ±45° reading, to be corrected by a new registration if it is wrong.
- **The binding.** LIVE-AUTHOR-0's, with A and D rebound to the strafes. W and Up step toward the nearest cardinal, S
  and Down away from it, A and Q to the cardinal 90° left, D and E 90° right. Space and 1–5 edit as before; the faced
  cell is the one ahead of the nearest cardinal. Left and Right stay quarter turns of the heading. W, A, S and D never
  change the heading.

**The session.** The one live session (`playback::LiveSession`) gains a heading and one event.

- **The look event.** Its parameter is the integer delta and its witness is the frame digest at the new heading. The
  facing is always the heading's nearest cardinal, so a step, a strafe and the faced cell mean what they meant. A
  quarter turn turns the heading with the facing. A session's base camera stays one of the four facings.
- **The frame.** At one of the four anchor headings it is the facing kernel's, as before, and the camera token keeps
  its letter, so a walk that never looks saves the bytes it always saved. At any other heading it is the bearing
  kernel's index frame at (x, z, k), and the token carries the id in decimal.
- **The fold.** A look folds with tag K over its camera token and its witness together:
  head′ = sha256(head : K : token : witness). A move and an edit fold as before.
- **The stamp.** A tick run saves, beside each event it appended, the tick it was applied at, and beside each look its
  inputs (counts, multiplier, step). The typed command sequence is the log grouped by tick. The session also saves its
  tick count and final sensitivity. Raw counts are never the meaning of a look: the delta is the event. A tick is when,
  not what: no world state depends on it, and the head does not cover it. Both verifiers check its form: the delta is
  counts × multiplier × step, ticks never decrease, and a timed look is the first event of its tick.
- **Certification at save.** Live, a frame at a free heading is rendered once, by BEARING-FAST-0's production tread
  (`ca`), through `shell/heading.rs`, the only file of the shell that reaches the bearing kernels. At save, before
  anything is written, every such frame is recomputed by the reference (`kernel/bearing.rs`: its traversal and its
  index frame) across threads. One difference refuses the save with `LIVESESSION-UNCERTIFIED`, and no session file is
  written. A crashed run's journal is what was flushed, not a saved session.
- **The verifiers.** The workshop's `sessionwalk` learns the look event (`sessionwalk look --delta D`), the heading
  token and the tick form, and renders with the reference alone. `verify/livesession.py`, the session sealer, learns
  the look's fold. `shell playback` shows the four facings and refuses a session that holds a look.

**The tick run.** `shell simtick-selftest --script …` is the rung's instrument: a script of raw inputs with their times
(`T:m+N`, `T:KEY`, `T:mult+`, `T:mult-`, `T:step`) goes through the accumulator, one command per tick, into the same
session, journal and seal the live editor uses. It has no surface, no loop and no present; a run is ledgered as
`livesession` on surface `none`. The seal is now one function, `finish`, shared by the loop's run and the tick run.

**What the gate holds (8 rows, 197 in all).**

- `simtick-law`. The shell prints its laws and a Python twin re-derives them, line for line: the tick boundaries
  (15,624 µs is tick 0, 15,625 µs is tick 1), the nearest cardinal of all 360,000 ids as one digest (each cardinal owns
  exactly 90,000; 44999 is N and 45000 is E, and so on round), the quarter-turn law at every id, the turn's wrap, the
  delta over a grid with its refusals, the sensitivity's ends, the rebinding. A build with the tie-break reversed, with
  the tick one microsecond short or long, or with a coarse step of 87 prints different lines.
- `simtick-script`. Script S, from 28,28,N on the witness level: 102 inputs in 28 ticks become 27 commands and 24
  events (13 looks, 9 moves of which 2 are blocked, 2 edits), with 3 refusals and 1 unbound key, each outcome equal to
  the twin's re-derivation from the script alone. It registers, among others: three reports summed in one tick; a
  report at exactly 15,625 µs belonging to tick 1; a zero-sum tick; a key that arrived before the report in its tick and
  still stepped toward the cardinal after the look; the tie at 45000 (east) and 44999 (north) reached in fine steps; a
  quarter turn, the strafes, Space and a class key at free headings; a negative look through 0; a look back to an
  anchor and a whole turn; the multiplier refused below 1 and above 64.
- `simtick-replay`. Every frame witness of the saved session equals the kernel executable's at that camera (20 of them
  at free headings, the bearing reference's), and the twin's fold is the saved head. The workshop verifies the file,
  and the same events authored in the workshop reach the same head, without ticks. A changed delta, input or camera
  token, a tick run backwards and a look stripped of its tick are each refused by both verifiers. So is a look moved
  consistently from heading 100 to 99, which the reference shows to have one index frame.
- `simtick-equivalence`. Script S with every input moved inside its own tick, and every tick's reports split or merged
  to the same sum, saves byte-identical data. The same commands at ticks 1000 + 3t save the same events, witnesses and
  head, and differ only in their tick fields and the tick count.
- `simtick-certify`. Script S's save recomputes its 20 free-heading frames with the reference and records it. A shell
  built with a planted defect in the fast path (the wall's bottom edge loses its ink, the same way live and on replay)
  is refused at the save, naming event 0, writes no session file and ends 2. Under that same shell a walk on the four
  facings saves, with zero frames to recompute.
- `simtick-resume`. S's saved session continues at tick 28 with its multiplier of 64, equal to the twin's own
  continuation. A session left at a free heading is refused by the window loop (`LIVEINPUT-HEADING`); looked back to
  north, the window loop continues it, its untimed events beside the timed ones. A tick run that died after five
  journaled events recovers its four looks and a move, and goes on at tick 5 with its last look's sensitivity.
- `simtick-fence`. `simtick.rs` is pure and holds the registered constants; the tick run applies the look once and
  first; `win32.rs` reads no mouse and still begins with LATENCY-0's instrument; the live loop binds no look and reads
  no clock; only `heading.rs` reaches the bearing kernels, and the workshop never reaches the fast path; the save
  certifies before it writes; `mantle.rs`, `fast.rs`, `formats.rs`, `hud.rs`, `vocab.rs`, `bearingfast.rs`, the
  reference's core and `shell/present.rs` are unchanged.
- `simtick-preregistered`. The entry's method phrases and its hash.

**Found while building.**

- **One index frame, two headings.** The first draft of the registration folded a look's witness alone, as a move's is
  folded. The first development run showed two looks ten ids apart with the same index frame (28,28 at 176 and at 166):
  the index frame holds material indices, and a turn of a hundredth of a degree in front of a near wall can leave every
  one of them where it was. That fold could not tell the two headings apart. The registration was revised once, before
  it left the build machine and before any gate row existed: a look now folds its camera token with its witness, and
  the row that would catch the difference is registered (`simtick-replay`, headings 100 and 99). The entry's commit
  message records the revision.
- **Ten mutations, ten caught.** Each was applied to a scratch copy and the named rows run: the look dropped from a
  command; the last report winning instead of the sum; the look folded without its token; certification skipped; the
  tick form unchecked on load; the loop's free-heading guard removed; the workshop ignoring stored camera tokens; a
  quarter turn leaving the heading; the workshop's tie-break reversed; resumed ticks restarting at zero. A first form
  of the fifth mutation was ineffective (the error still propagated) and was repaired before it counted.
- **Seven earlier fences re-pinned on purpose**, each with a comment at its pin: `allocreuse1-lock` (the move's witness
  is taken through `heading.rs`, the same `compose_frame` at an anchor), `liveinput-fence` (the same, and the loop now
  reads the heading to refuse a free one), `livesession-preregistered` (the renderer identity's five sources are read
  inside their own list, now that the bearing identity has a second), `livesession-fence` (the seal is `finish`),
  `liveauthor-fence` (its section is bounded at the next), `bearing-fence` (`heading.rs` and the workshop's verifier
  use the reference; no window does) and `bearingfast-fence` (`heading.rs` reaches the fast path; no window does). No
  behavioural row of LIVE-INPUT-0, LIVE-SESSION-0, LIVE-AUTHOR-0 or HOLD-WALK-0 moved.
- **The window build was type-checked here, not run.** No Windows target is installed in the build container, so the
  windowed shell was type-checked in a scratch copy with the platform switch flipped. It was not linked or run here;
  the host build was the test, and it is recorded below.

**On the owner's host (2026-10-02).** The registration was applied and pushed first, alone (`87b152b`); then the build
(`998dbe4`).

- **The gate.** `GATE PASSED`, 197 rows, none failed and none skipped, rowset `b2dd25aedf2b0c32`: the same rows and the
  same rowset as in the build container. The eight `simtick-*` rows ran there on Windows, with the host's committed
  records present.
- **The window build.** `rustc -O --cfg shell_window shell\main.rs` compiled with no error and no warning. This is the
  first time the changed session code was linked into the window.
- **A walk in the live editor**, `shell live-window`, to see that the window loop behaves as it did. The owner pressed
  47 keys from 28,28,N: 46 moves (2 of them blocked) and Esc, with no key held and no edit. The loop rendered and
  presented 1,034 compositions, checked the bytes of every one, and read the screen back 50 times; none differed. The
  walk ended at 7,26,W and was saved and verified: 46 events, head `7815732d91dc…`. Every heading in it is one of the
  four facings, so the save had no free-heading frame to recompute and printed no certification line. That is the
  registered behaviour: a walk with no look saves as before.

The walk is the console's account of one run. It is not a sealed record and nothing was committed from it; the saved
session stays under `build/sessions/` on the host.

**Amended by SIM-TICK-0a.** A sensitivity action that takes effect is now a typed configuration event in the log,
never folded, and a held key's repeats walk at most once a tick. The section below this one has the rules. What is
said above about a sensitivity action leaving no event describes this rung as it was registered and run on the host.

**Grade.** DECLARED: the tick, the command, the delta, the nearest cardinal (the ±45° reading), the binding, the fold,
ticks as recorded and never authority, certification at save. ESTABLISHED (gate, in the build container and on the
owner's host): the eight rows above, and every earlier row beside them. MEASURED: nothing; this rung takes no number.
The host walk is an observation of one run, not a record. NOT_MEASURED: how a real mouse's reports reach a tick, any
latency or feel, and how long a long session takes to certify at save.

**does_not_show.** That mouse-look works on the host: nothing here reads a mouse, a clock or a window, and the host
walk held no look. The window has not shown a free heading; a session left at one is still refused by the window loop. Any feel,
latency or frame rate. That the tick index is authority: it is recorded, sealed with the file and checked for form, and
the same commands at other ticks reach the same head. That the head pins every heading: a look's heading is folded; a
move's camera is still re-derived by replay, as it always was. Anything about a picture on the screen at a free
heading: the witness is the index frame's digest, and the picture alone, with no overlay, is MOUSE-LOOK-0's.

**Falsifier.** `simtick-law` goes red if any law line differs from the twin's, or a mutant build is not caught.
`simtick-script` goes red if any outcome, event, tick or input of script S differs. `simtick-replay` goes red if a
witness is not the kernel executable's, if the workshop disagrees, if a tamper is accepted, or if two looks to different
headings fold to one head. `simtick-equivalence` goes red if timing inside a tick, or the tick index, changes the data
or the head. `simtick-certify` goes red if a defective fast path can save. `simtick-resume` goes red if a continuation
loses its heading, tick count or sensitivity, or the window loop shows a free heading. `simtick-fence` goes red if a
clock, a float, a mouse or a window enters the rule proof, or a renderer source changes.

## SIM-TICK-0a — sensitivity as a typed configuration event; held keys by the tick (preregistered and built; an amendment to SIM-TICK-0; the gate passes on the host)

**Why.** MOUSE-LOOK-0's court was held on 2026-10-02. Two of the owner's four rulings there are not about a window at
all: they are rules of the tick. The owner had ruled that SIM-TICK-0 stays completely windowless and that the two rungs
are never combined, so those two rulings are taken here, with no window, no clock and no Win32 input, before
MOUSE-LOOK-0 puts a real mouse on them. SIM-TICK-0's entry (`dc1dddf2`) is not edited; this rung has its own
(`471f4d72`).

**The court's four rulings.**

- **Capture is shell state, never session state** (for MOUSE-LOOK-0). The mouse is captured from the start until Esc,
  the cursor hidden and confined, and raw counts feed the tick's accumulator while the window is in the foreground.
  Alt-Tab releases the mouse and pauses the look; returning recaptures it. No look of zero, no pause event and no
  synthetic input is ever made by a focus change. Esc releases, then saves, then the reference recomputes. The
  owner's words: the shell owns where the mouse is allowed to speak; the session owns what the mouse actually said.
- **PgUp, PgDn and Tab change the sensitivity, and the change is a typed configuration event** (taken here). The keys
  are physical bindings at the shell level. Their effects, not the keys, are what the session records. A change takes
  effect at the next tick and is itself in the session's command stream, so the session remembers the configuration
  transitions and not only the heading they produced. The vocabulary is then LOOK (mouse), MOVE (W, A, S, D), EDIT
  (Space, 1–5), SENSITIVITY (PgUp, PgDn, Tab) and SHELL CONTROL (Esc, focus, capture).
- **A held key walks once a tick** (taken here). HOLD-WALK-0's law stands, with the tick as the coalescing boundary:
  keyboard repeat frequency is input production, 64 Hz is simulation authority.
- **The live sample is every 64th free-heading frame, off the loop** (for MOUSE-LOOK-0). The reference recomputes it
  on a worker thread, a mismatch ends the run refused, and the save still recomputes every frame.

**The rules, registered before the build.**

- **The sensitivity event.** A sensitivity action that takes effect is appended to the log as one event of kind
  `sensitivity`. It carries the configuration after it (the multiplier and the step) and the tick it was applied at.
  A refused action (below 1, above 64) is still no event.
- **Configuration, not world.** The event has no witness and it is not folded: the head after it is the head before
  it. The head is the worldline's, frames and content, and the same world reached under another sensitivity is the
  same worldline. One consequence was chosen on purpose: pressing PgUp does not move the head, so it cannot invalidate
  anything anchored to a head.
- **Replayed state.** The session owns the configuration, as it owns the camera. It starts at multiplier 1, step 88.
  Only a sensitivity event changes it, by exactly one legal transition: the multiplier one up or one down inside 1 to
  64, or the step toggled between 88 and 1. A timed look's inputs must carry the configuration in force when it was
  applied, and the session's tick block must carry the configuration at the end. Both verifiers replay it.
- **The binding.** A pure map from a key code: PgUp is multiplier up, PgDn multiplier down, Tab the step toggle.
  Reading those keys from the window is MOUSE-LOOK-0's.
- **Held keys.** A fresh press always acts and is never coalesced. An auto-repeated press of a key in HOLD-WALK-0's
  held set (W, A, S, D and the four arrows) is bound as that key's press, but only the first repeat in a tick. Every
  later repeat in that tick, of any held key, is coalesced: counted and traced, never an event. A repeat of any other
  key is ignored and counted, so holding Space, a class key or PgUp acts once. Nothing about a repeat is saved; a
  walked repeat's move is an ordinary move.

**What this amends.** SIM-TICK-0 said a sensitivity action is not an event and is saved only inside the looks that
follow it. It is still not a world event; it is now a configuration event in the log. SIM-TICK-0's rows were re-pinned
on purpose for that and are named at their pins: script S's saved log now holds its 68 sensitivity events between its
24 world events, the look moved to a neighbouring heading is event 1 of its file and not event 0, and a continuation's
lowered multiplier is its own event. Script S's head did not change (`3aa992fc70bf…`), which is the rule working. A
crashed run's journal now recovers the configuration exactly from its sensitivity events, where before it took the
last look's. A tick session saved in SIM-TICK-0's form, a look carrying a changed multiplier with no sensitivity event
before it, no longer loads. None exists outside the gate's scratch: no window has made a look.

**What the gate holds (4 rows, 201 in all).**

- `simtick0a-config`. The owner's sequence, PgUp, mouse, Tab, mouse, PgDn, saves a sensitivity event (2, 88), a look
  carrying 2 and 88, a sensitivity event (2, 1), a look carrying 2 and 1, and a sensitivity event (1, 1), as the twin
  re-derives. The head moves at the two looks and at no sensitivity event. The same two looks from other counts, with
  no sensitivity change, save a different log and the same head. Eight forgeries are each refused by both verifiers: a
  sensitivity event removed, two steps at once, a multiplier of 0 or 65, a step of 87, a missing tick, a tick block
  that is not the final configuration, and a look whose inputs multiply to its delta under another configuration. A
  run that died after a PgUp and a Tab made after its last look comes back at multiplier 3, step 1, and its next look
  uses them.
- `simtick0a-hold`. Script R: 30 key presses, 24 of them auto-repeats. 8 repeats walk, never two in one tick; 10 are
  coalesced; 6 are ignored (Space, a class key, Q, E, PgUp, Tab). A fresh press and a repeat in one tick both act;
  three repeats in a tick are one step; a burst of six, as after a slow frame, is one step. Nothing about a repeat is
  in the saved session, and the same walk with each walked repeat pressed saves byte-identical data.
- `simtick0a-fence`. The session's sensitivity event is one legal transition, folds nothing and writes no W, M or
  camera; every fold (the shell's, the workshop's, the sealer's) skips it; the tick run keeps no sensitivity of its
  own; the accumulator admits one held repeat a tick under HOLD-WALK-0's own set; the editor's bindings and the window
  loop do not know the control keys; `win32.rs` reads no mouse and confines no cursor.
- `simtick0a-preregistered`. The entry's method phrases, and SIM-TICK-0's entry still at its registered hash.

**Found while building.**

- **Two mutations slipped through the first form of the configuration row, and the row was strengthened.** Eight
  mutations were applied to scratch copies. A shell, and then a workshop, with the configuration-in-force check removed
  both still passed: every forgery in the row was also an illegal transition, so that check was never the only thing
  refusing. A forgery that isolates it was added, a look whose inputs multiply to the same delta under another
  configuration (6 × 1 × 88 for 3 × 2 × 88), and both mutants are now caught. The other six were caught at once: the
  sensitivity event folded into the head, every held repeat walking, a journal recovering its last look's
  sensitivity, Tab raising the multiplier, every key treated as held, and the session accepting an illegal transition.
- **`shell playback` refuses a session that holds a sensitivity event**, as it refuses one that holds a look. It
  replays moves and edits on the four facings. Playback of a tick session is not built.

**On the owner's host (2026-10-02).** The registration was pushed first, with LLM-BUILDER-0's declaration
(`2c5fa11`); then the build (`322970f`).

- **The gate.** `GATE PASSED`, 201 rows, none failed and none skipped, rowset `e17a948eb19f7f92`: the same rows and
  rowset as in the build container.
- **An informal timing of a look, taken to size MOUSE-LOOK-0.** One windowless tick run of 640 looks, one a tick (ten
  seconds of continuous looking, one count each at multiplier 1 and step 88), through `shell simtick-selftest` in the
  gate's own build, timed from outside with PowerShell's `Measure-Command`: **13.26 s** for the whole process. That is
  20.7 ms per look, summed over everything the run does for it: the live path (the scene composed, the frame rendered
  once by the production tread, its digest, the event journaled and flushed), the reference's recomputation of all 640
  frames across threads at the save, and the saved file's replay (each frame rendered and digested again), plus the
  process's start and the file's writing. The run saved, so all 640 frames were equal under the reference.
  - **What it is.** One run, one wall-clock number, taken once. It is not a sealed record and no rule reads it.
  - **What it bounds.** No phase of a look can cost more than the sum, so the live path of a look is under 20.7 ms on
    this host, and a ten-second look saves in under 13.3 s after it ends.
  - **What it does not say.** How the 20.7 ms splits between the live path, the reference and the replay; whether the
    live path fits inside one 15,625 µs tick; anything about a window, a blit or a present. A split needs a clock
    inside the run, and this rung has none.

**Grade.** DECLARED: the sensitivity event and its not being folded, the configuration as replayed state, the binding,
the tick as the coalescing boundary. ESTABLISHED (gate, in the build container and on the owner's host): the four rows
above and SIM-TICK-0's rows under the amended form. MEASURED: nothing sealed; the timing above is an observation of one
run. NOT_MEASURED: anything about a window, a real key or a real mouse, and the cost of a look phase by phase.

**does_not_show.** That the keys work in the window: the map is from a key code, and nothing here reads one. That the
head covers the settings a world was walked under: it does not, on purpose, and a legal transition added and undone
between two looks is caught by the file's seal and by nothing else. Anything about capture, focus or the cursor: that
ruling is recorded above and built in MOUSE-LOOK-0. How fast a held key walks on the host: the keyboard's repeat rate,
capped at one step a tick, is not observed here.

**Falsifier.** `simtick0a-config` goes red if a sensitivity change that takes effect leaves no event, if a head moves
at one, if two sessions with the same world events have different heads, if a forgery is accepted, or if a journal
loses a configuration change. `simtick0a-hold` goes red if two repeats walk in one tick, a fresh press is coalesced,
a repeat of another key acts, or a held walk's data differs from the same walk pressed. `simtick0a-fence` goes red if
the event folds or touches the world, if the tick run keeps its own sensitivity, or if a window reads a mouse.

## MOUSE-LOOK-0 — a real mouse on the locked tick rules: the live editor with mouse-look (preregistered and built; the gate passes on the host; on the second host run, under MOUSE-LOOK-0a, a real mouse turned the camera: 1,761 looks, every free-heading frame the reference's)

**Why.** The fourth rung of the owner's ladder: real mouse → 64 Hz accumulator → command → the existing live loop.
The rules were locked windowless first (SIM-TICK-0, SIM-TICK-0a), and they are not proved again here. This rung adds
only what they left out: the clock, the mouse, the capture, and the loop presenting a free heading. Registered before
the build (`60870497`), and the registration was cut as its own patch to be pushed first.

**The owner's rulings.** The four from the court of 2026-10-02 are recorded under SIM-TICK-0a above. Two of them are
built here: capture is shell state and never session state, and the reference samples every 64th free-heading frame
off the loop. One more was asked for this rung and answered:

- **A new command, `look-window`.** The live editor with the mouse is its own entry (`shell look-window` on the host,
  `shell look-selftest` on the mock) on the same loop function, session, journal and seal. `shell live-window` and
  every earlier command stay exactly as registered and are given no tick source.

**The rules, registered before the build.**

- **The clock.** An input's tick is the tick of the microsecond at which the loop drained it. In the window that is
  QueryPerformanceCounter since the loop's first composition; on the mock it is the composition count times 13,333 µs.
  A tick's command is applied at the first composition whose clock has passed the tick's end.
- **The mouse.** Windows raw input (WM_INPUT): the relative horizontal count, as the device reports it. Nothing else
  of the mouse is read. The pointer's position is never used as counts.
- **Capture.** While the window is the foreground window the cursor is hidden and confined to it, and what arrives is
  admitted. When it is not, the mouse is released and nothing is admitted. Returning recaptures. No focus or capture
  change makes a session event of any kind: no look of zero, no pause, no synthetic input. Esc releases, then saves,
  then the reference recomputes.
- **The picture.** At a free heading the loop presents the picture alone: the session's own render of that state by
  the production tread, the render its witness came from, rendered once, with no overlay. At an anchor it presents
  the composite as before.
- **The readback** under ticks is sampled: the first composition and every 75th after it.
- **The live sample.** Every 64th frame event at a free heading in the run is recomputed by the reference on a worker
  thread. A mismatch ends the run refused and nothing is saved. A sample certifies nothing; the save still recomputes
  every free-heading frame.
- **The beat.** 64 ticks a second against 75 compositions means some compositions repeat the picture before them.
  They are counted on every run and nothing is done about them here.

**What was built.**

- `shell/mouselook.rs`, new. The tick source's trait (a clock, the admitted counts, the release). The ticker: each
  composition it closes the tick the clock has passed and applies that tick's command through the tick run's own
  function (`tickrun::apply`), then stamps what the composition drained with the tick of now and feeds it to the
  accumulator. It appends nothing itself. The sampler: one thread per 64th free-heading frame, read back oldest first
  so the first difference reported is the earliest. The mock: a scripted mouse, keyboard and focus (`T:m+N`, `T:KEY`,
  `T:KEY+`, `T:blur`, `T:focus`) and a clock that is the composition count.
- `shell/liveinput.rs`. The loop takes an optional tick source. `run` and `run_with` pass none and are the loop they
  were; `run_look` passes one. Under a tick source the presses and reports go to the ticker in one block, which is the
  only place the clock is read; at a free heading the loop presents the session's picture and renders nothing; at an
  anchor it renders, checks and presents the composite as before, and holds the reference to the last frame event's
  witness as it does for a pressed move.
- `shell/heading.rs` and `shell/playback.rs`. The session keeps a painter: the one render that witnesses a free-heading
  frame is made into buffers the session reuses, and its picture stays readable. If the world is edited while the
  heading is free (no frame event), the picture is rendered once for the new world when the loop asks for it.
- `shell/tickrun.rs`. `apply` is public, so the ticker and the windowless run apply a command through the same code.
- `shell/livesession.rs`. `go_look`: the loop, the release, then the shared seal. The saved file's live block gains a
  `look` object for such a run: the compositions, how many showed the picture and how many the composite, how many
  repeated, the readbacks, the samples.
- `shell/win32.rs`, a section appended last: raw input, the cursor's capture and release by the foreground, the
  clock, and `look_window`.
- `verify/livesession.py` cites this entry, with SIM-TICK-0 and SIM-TICK-0a, for a session whose live block carries
  the look loop's counts.

**What the gate holds (6 rows, 207 in all).**

- `mouselook-loop`. Script L: 26 inputs (14 mouse reports, 12 key presses) at times that are multiples of nothing,
  from 28,28,N. Each is stamped with the tick of the composition that drained it, and the saved data is byte-identical
  to what `shell simtick-selftest` saves from the same inputs at those times, so the window loop adds nothing to the
  rules. Two compositions inside one tick make one look of the summed counts. Of 155 compositions 128 presented the
  session's picture and 27 the composite, 133 repeated the picture before them, and the clock never moved more than
  one tick between two, all as a Python model of the schedule derives. The workshop verifies the file.
- `mouselook-capture`. The same script with the window out of the foreground from tick 26 to tick 41, and six inputs
  arriving meanwhile (mouse motion, W, Space, PgUp, an Esc). The saved data is byte-identical and the loop showed the
  same 155 compositions. All six are dropped and counted in the live block, none is an event, no event carries a tick
  inside the stretch, and the session's data holds no word of the focus. The mouse is released before the save
  begins. As a control, the same six inputs with the window in the foreground do change the session.
- `mouselook-present`. At the three read-back compositions (0, 75 and 150) the sha256 of the picture handed to the
  call is the kernel executable's: the composite at 28,28,N (the one LIVE-INPUT-0's loop presents there), the bearing
  reference's picture alone at 30,28,314912 in the edited world, and the composite again at 29,28,W. Composition 75
  follows a floor repaint that made no frame event, and the row checks that the repaint shows there, so a stale
  picture would be seen. A surface whose call writes nothing completes with all three readbacks counted, logged and
  recorded as differing, and the same session saved.
- `mouselook-sample`. The steady script: a report at every composition, 136 looks at free headings. Exactly two
  samples, one per 64 frames, both equal, and the save still recomputes all 136. With an input at every composition,
  11 of compositions 76 to 150 close no tick and repeat the picture before them. A shell built with the planted,
  self-consistent fast-path defect is refused by its first sample (LIVEINPUT-SAMPLE, event 63, the 64th free-heading
  frame), releases the mouse, writes no session file and ends 2 with one refusal-log record.
- `mouselook-fence`. The clockless entry points pass no tick source. The loop reads the clock and the mouse only
  through one, in one block. Only `run_look` gives one, only `go_look` calls it, and only `look-selftest` and
  `look-window` call `go_look`. The ticker closes a tick before it feeds the composition's inputs and appends nothing
  itself. The mouse is released before the seal. The window section is the last one in `shell/win32.rs`, admits only
  captured keys and relative horizontal raw counts, reads its clock in one place, calls no session method, reaches no
  renderer and writes nothing. `simtick.rs`, the kernels and `present.rs` are what they were.
- `mouselook-preregistered`. The entry's method phrases, and SIM-TICK-0's and SIM-TICK-0a's entries at their hashes.

Five earlier fences were re-pinned on purpose, each named at its pin: `liveinput-fence` and `holdwalk-fence` (the
presses the loop binds are the surface's or, under a tick source, none; what is presented is the checked composite
or, at a free heading under a tick source, the session's picture), `livesession-fence` (`go_look` records its
surface's observation too), and `simtick-fence` and `simtick0a-fence` (raw input and the cursor's confinement exist
now, in this rung's section only; the witness is a method of the session's painter).

**Found while building.**

- **A registered limit names a mechanism the registered clock rule excludes.** The entry's limits say that a loop
  which falls behind "applies several ticks' commands in one composition" and that "the largest such burst is counted".
  Under the entry's own clock rule that cannot happen: every input a composition drains takes that composition's tick,
  so one tick is open at a time and a composition applies at most one command. What a slow loop does instead is gather
  a longer stretch of inputs into one tick. The entry is not edited. What is counted and saved is the `span`: the most
  ticks the clock moved between two compositions, 1 on a loop that keeps up and more on one that falls behind.
- **Twenty mutations, all caught at once.** Applied to scratch copies: the mock admitting inputs while out of the
  foreground; an input stamped with the next tick; a tick's command applied before its tick ended; the composite
  presented at a free heading; the picture not rendered again after an edit at a free heading; a sample every 65th
  frame; a differing sample ignored; a readback every 74th composition; the mouse not released before the seal; the
  ticker with no held set; the mock's clock one composition ahead; the presses bound by the clockless loop under a
  tick source; the live block not recording the loop; a focus change making an input; the picture presented with
  stale overlay bytes; repeated compositions miscounted; the window admitting counts while not captured; the window
  reading the vertical count; a clockless entry point reading the clock; the ticker appending an event of its own.
  With the differing sample ignored, the planted shell was still refused, at the save (LIVESESSION-UNCERTIFIED): the
  sample is an earlier refusal, and the save's recomputation is the one that decides.
- **Key presses are dropped while the window is out of the foreground, as mouse counts are.** A window without the
  foreground receives no key presses in practice. The window section applies the same rule to a press as to a count,
  and counts what it drops, so the mock and the window say the same thing.
- **The sealer does not read the focus observation.** LIVE-SESSION-0's fence forbids it: the observation is recorded,
  never ruled on. So the loop's own counts go into a separate `look` object in the live block, and the sealer cites
  this entry when that object is there. A windowless tick run's file has none and is cited as before.
- **What "repeated" counts.** A composition at which no event was applied. A blocked step or a sensitivity change is
  an event, so its composition is not counted as a repeat even where the picture comes out equal.
- **The witness check at an anchor under ticks is parity, not held by a row.** When a tick's command leaves the heading
  on an anchor and its last event is a frame event, the loop requires its reference of the new state to reproduce that
  event's witness, as it does for a pressed move. No row plants a defect there.
- **The mock's period is a third of a microsecond short of a 75th of a second.** 13,333 µs, so 75 compositions span
  just under 64 ticks and a stretch of 75 repeats 11 or 12, not always 11. The row states which stretch it counts.
- **How the window section was checked here.** A scratch copy of the tree with the shell's `target_os = "windows"`
  conditions turned to this host's, then `rustc --cfg shell_window --emit=metadata`: no error and no warning. That
  checks types and names against the declarations in the file. It does not link, and it runs nothing.

**On the owner's host (2026-10-02): the gate, and the first run of the window.** The registration was pushed first,
with SIM-TICK-0a's host note (`422388c`); then the build (`8041070`).

- **The gate.** `GATE PASSED`, 207 rows, none failed and none skipped, rowset `188ac5ddbce45680`: the same rows and
  rowset as in the build container.
- **The window build.** `rustc -O --cfg shell_window` compiled with no output. That is the window section's first
  compile and link on Windows.
- **The run.** One run of `shell look-window`, 1,873 ticks long by the window's own clock.
  - *The window and the capture.* The window held the foreground at the start and at every one of its 1,828 pumps. The
    mouse was captured once and released once.
  - *The keys, on the tick.* 48 key presses, each stamped with a tick read from QueryPerformanceCounter, made 48
    commands and 47 events: 37 moves (17 of them blocked) and 10 edits (8 cells opened or closed, 2 tile classes
    painted). A and D strafed, as the tick's binding has them. Esc, at tick 1,872, ended the run.
  - *The screen.* 1,826 compositions, all of the composite, each rendered through the `LoopRenderer` and checked
    against its reference; 48 references; 25 screen readbacks (the first composition and every 75th after it), none
    differing.
  - *The save.* Released, then saved and verified by the shell: 47 events, head `e9dafb482675…`. The live block
    carries the loop's counts.
- **What the run did not show: a look.** No mouse report reached the loop. The live block reads reports 0, dropped 0,
  absolute 0, and the session holds no look; the heading never left north. So no picture was presented at a free
  heading (picture 0), no sample was taken (samples 0), and the save had no free-heading frame to recompute
  (certified 0). The rung's own question, whether a real mouse turns the camera, is not answered by this run.
  - *Why is not known.* The record cannot say whether the mouse was moved. If it was, then either no raw input
    message arrived, or one arrived and was not read; the window section counts neither case. It counts the reports
    it admits, the ones it drops while not captured, and the absolute ones, and nothing before that point. That is a
    gap in the observation, found by this run.
- **What the run did not exercise.** The window never left the foreground (0 changes), so nothing is shown about a
  focus loss or a recapture. No sensitivity key was pressed, no key was held long enough to repeat, and no arrow was
  pressed.
- **Found: the saved file says the run ended `closed`, and the tick run says `escape`.** Both lines are in the same
  output. The presenter's window procedure, which this window shares, destroys the window when Esc is pressed. So in
  the pump that reads the Esc the window is already gone: the loop sees a closed window with the Esc's tick still
  open, ends there, and the tick is closed and its command applied as the run finishes. The session is right (the
  Esc ended it, 47 events, tick count 1,873). The label in the live block is not, and the mock did not model this:
  its Esc was applied a composition or two later, with the window still open.
- **The beat, as counted.** 1,826 compositions against 1,873 ticks, 1,778 of them repeating the picture before them
  (every composition at which no key's event was applied), and a span of 7: at least once, seven ticks passed between
  two compositions. The loop did not keep to the tick schedule everywhere. Nothing is concluded from that here and
  nothing is changed because of it: why, and what it costs on the screen, is the next rung's measurement.

**Against the eight points the owner asked of the first host run.**

| # | The point | This run |
|---|---|---|
| 1 | A real mouse produces real look events | Not shown: no mouse report reached the loop. |
| 2 | A focus loss produces no session event | Not exercised: the window never left the foreground. |
| 3 | Returning focus recaptures | Not exercised. |
| 4 | Esc releases before the save | Shown: the release is printed before the save, and the live block reads releases 1, released true. |
| 5 | The saved session certifies completely | Vacuous: there was no free-heading frame to recompute. The shell's own replay of the saved file verified. |
| 6 | No overlay at a free heading | Not exercised: no free heading was reached. |
| 7 | The live render and the reference agree | Not exercised for the bearing path. On the four facings: 1,826 byte checks and 25 screen readbacks, none differing. |
| 8 | No latency claim | None is made. |

**The owner's rulings after the build (2026-10-02).**

- **The registered limit's wording is to be corrected, not only counted differently.** `span` is the useful
  quantity, but it does not make the entry's statement about several commands in one composition true. The owner's
  wording: a composition applies at most one closed tick command; `span` records the largest number of tick
  boundaries between consecutive compositions; a span above 1 means the loop fell behind the tick schedule and does
  not mean several commands were applied in that composition. Entries here are never edited after registration, so
  the correction is an amendment with its own entry, MOUSE-LOOK-0a, as LATENCY-1a and SIM-TICK-0a were.
- **The check with no row gets a row only if it asserts a semantic invariant.** It does not. It recomputes, at an
  anchor, a frame the event already witnessed and compares the two digests. The shell's replay of the saved file, the
  workshop and the sealer each verify the same witnesses again before a session counts. It is an earlier refusal of
  something those would refuse anyway, so it stays a sanity check, and no row is added for it.
- **The implementation is locked and nothing is optimized from the first run.** The host run is this rung's
  execution witness, not a latency measurement.

**Grade.** DECLARED: the entry point, the drain-time clock rule, capture as shell state, the picture alone at a free
heading, the two sampling periods. ESTABLISHED (gate, in the build container and on the owner's host): the six rows
above, over the mock. MEASURED (the first host run, sealed: `livesession-DANIELDILLBERG-e9dafb482675.json`): the
window, the capture taken and released, key presses stamped by the window's clock and applied on the tick, the
composite read back exact, the save; no look. MEASURED (the second host run, under MOUSE-LOOK-0a, sealed and
recorded in that section): a real mouse making looks, a focus loss with no session event, the picture at a free
heading, the samples and the save's certification. NOT_MEASURED: latency; what a look costs phase by phase.

**does_not_show.** Any latency: by design an input is
applied up to one tick and one composition after it is drained, and what that costs on the screen is the next rung's
measurement. When the device moved: an input's tick is the tick it was drained in. That a run was right because its
samples were equal: one frame in 64 is sampled, and only the save's recomputation is exhaustive. That the screen
showed every picture: one composition in 75 is read back. Counts per degree: they depend on the mouse and are not
normalized.

**Falsifier.** `mouselook-loop` goes red if the look loop's saved data differs from the windowless run's on the same
inputs at their drain times, or its compositions are not the schedule's. `mouselook-capture` goes red if anything
arriving while the window is away reaches the session, or the mouse is still held when the save begins.
`mouselook-present` goes red if a read-back picture is not the kernel executable's at that camera, or a differing
screen is not counted. `mouselook-sample` goes red if the samples are not one per 64, or a defective fast path is not
refused by its first sample. `mouselook-fence` goes red if a clockless entry point is given a tick source, the clock
is read anywhere else, the ticker appends an event, or the window section calls the session or a renderer. On the
host: a look that turns the wrong way, a walk that Alt-Tab changes, or a saved session the workshop refuses.

## MOUSE-LOOK-0a — the timing limit's wording corrected; a run's end and the window's observation, from the first host run (preregistered and built; an amendment to MOUSE-LOOK-0; the gate passes on the host, and the second host run is the rung's execution witness)

**Why.** Two things. The owner ruled that a sentence in MOUSE-LOOK-0's entry be corrected, not only counted around.
And the first host run of `shell look-window` found two things the mock had not: the saved file mislabelled how the
run ended, and the window section could not say whether raw input had arrived. MOUSE-LOOK-0's entry (`60870497`) is
not edited; this amendment has its own (`3778b592`), registered and cut as its own patch.

**When it was registered.** After the first host run. That run's counts (no mouse report, a span of 7, an end
labelled `closed`) were seen before this entry was written. No condition in it reads those counts, no rule of the
tick or the loop changes, and nothing is optimized from the run.

**What it registers.**

- **The timing limit, in the owner's wording.** A composition applies at most one closed tick command. `span`
  records the largest number of tick boundaries between consecutive compositions. A span above 1 therefore indicates
  the loop fell behind the tick schedule; it does not imply multiple commands were applied in that composition.
  MOUSE-LOOK-0's limit that a slow loop "applies several ticks' commands in one composition", with "the largest such
  burst" counted, is withdrawn: under that entry's own clock rule it cannot happen.
- **The end of a run.** When the run ends, by Esc or by the window closing, the tick still open is closed there and
  its command applied, as the windowless tick run does at the end of its script. That is the one case in which a
  command is applied before the clock has passed its tick's end. On the host the presenter's window procedure
  destroys the window when Esc is pressed, in the pump that reads it, so the loop ends at that composition. A run its
  Esc ended is recorded as ended by `escape`, whatever the loop saw of the window; a run whose window closed with no
  Esc is recorded `closed`. The mock closes its window at an admitted Esc, as the host's does, and delivers nothing
  scripted after it.
- **The window's observation of the mouse, extended.** Beside the reports it admits, drops and finds absolute, the
  window section counts every raw input message it receives, every one it could not read as a mouse report (with the
  size the last such read returned), and every relative report whose horizontal count is zero. A read counts as a
  mouse report when it succeeds, holds at least the mouse structure and names the mouse type, whatever exact size it
  returns; before, the size had to be exactly the structure's, and a read of any other size was skipped without a
  count. The run prints the observation when it ends. It is observation only: nothing but a captured, relative,
  horizontal count is ever handed to the loop.
- **The sealer's reading.** A session run under the tick source is described as that, with its look count. One that
  holds no look is said to hold none.

**What the gate holds (2 rows, 209 in all).**

- `mouselook0a-ending`. Four scripts, each also run through `shell simtick-selftest` on the same inputs at their
  drain times, each saving byte-identical data and printing the observation it recorded. A key and an Esc drained
  by composition 16 end the run there, 16 compositions presented, the key's move an event of the Esc's tick, and
  nothing scripted after the Esc delivered: `escape` in the loop's output and in the live block. A script with no Esc
  ends `closed` in both. An auto-repeated Esc closes the window and, ignored by the tick's rules, ends the run
  `closed`. A keys-only session, as the first host run was, is sealed citing MOUSE-LOOK-0 as holding no look.
- `mouselook0a-preregistered`. The entry's method phrases; MOUSE-LOOK-0's entry at its hash, the withdrawn sentence
  still in it.
- MOUSE-LOOK-0's rows hold under the mock that closes at Esc, re-derived by the model: script L now presents 154
  compositions (128 the picture, 26 the composite, 132 repeated) where it presented 155, because the composition that
  drains the Esc is not presented; the steady script presents 162. `mouselook-fence` is re-pinned on purpose for the
  section's new counters and for the printed observation.

**Found while building.**

- **Seven mutations, all caught at once.** Applied to scratch copies: a run its Esc ended recorded as closed; the
  mock's window staying open at an Esc; the tick still open at the end dropped; a raw input message counted only after
  it was read; the sealer saying a keys-only session looked; an unread raw input message handed on as a count; the run
  not printing the observation.
- **Nothing shows the old read was what failed.** It required the returned size to be exactly the structure's, and
  skipped anything else without a count. A mouse report on this platform is expected to be exactly that size, so the
  old read may well have been right, and then the cause is elsewhere. It was changed because a skipped read was
  invisible, not because it is known to be the fault.
- **The first host session replays here.** The saved file of the first `look-window` run, read from the owner's
  folder, is verified by the workshop built in the container (head `e9dafb482675…`, 37 moves, 10 edits). With the
  amended sealer, in a scratch copy, its reading says it was run under the tick source holding no look and ended
  `closed`, which is the label that file carries. The record itself is the owner's to seal, on his host.
- **The model had the same blind spot as the mock.** The gate's twin counted the frames at free headings only for
  ticks closed at a composition. The tick applied as the run ends has frames too, and they are sampled like any
  other; the twin now counts them.

**What the next host run was for.** The observation line, written before the run. If `raw_messages` is zero after
the mouse has been moved, raw input is not arriving at the window, and the cause is in the registration or the device.
If it is not zero and `unread` is, the reads failed, and `unread_size` says what they returned. If `reports` is not
zero, looks were made, and the run is the rung's execution witness. Whichever it is, the run is recorded.

**On the owner's host (2026-10-03): the gate, the first session sealed, and the second run of the window.** The
host note and the registration were pushed first (`82e7799`), then the build (`2c4c155`).

- **The gate.** `GATE PASSED`, 209 rows, none failed and none skipped, rowset `a15345720a81009c`: the same rows and
  rowset as in the build container.
- **The first run's session, sealed.** `shell/attest/livesession-DANIELDILLBERG-e9dafb482675.json` (`82b1627`). Its
  reading says what the file carries: run under the tick source, holding no look, ended `closed`.
- **The second run.** `shell look-window`, 5,470 ticks long by the window's clock. A real mouse turned the camera.
  - *The observation adds up.* 14,867 raw input messages arrived: 13,931 relative reports with a horizontal count,
    all admitted, and 936 with none. None was unread, none absolute, none dropped.
  - *The looks.* The 13,931 reports became 1,761 looks, at most one in a tick and always the first event of its
    tick, none of zero. A tick's counts ran from −939 to 457. Every multiplier from 1 to 14 and both steps were used:
    57 sensitivity events, and 28 presses of PgDn at multiplier 1 refused, each one record and no event.
  - *The walk.* 14 moves, none blocked, with A strafing. W held: 4 repeats walked, one in each of ticks 333, 334, 336
    and 338, never two in a tick. 20 repeats of other keys were ignored.
  - *The focus.* The window left the foreground once and came back: 2 changes, 404 compositions without the
    foreground, the mouse captured twice and released twice. While it was away Windows delivered nothing to it
    (dropped 0, dropped keys 0), so the section's own drop was not exercised here; it is exercised on the mock. The
    log holds looks, moves and sensitivity changes and nothing else (1,832 = 1,761 + 14 + 57). The stretch away lies
    inside ticks 1,064 to 1,560, the session's longest stretch with no event and the only one long enough to hold
    404 compositions, so no event carries a tick inside it.
  - *The picture.* 4,649 compositions: 4,541 presented the session's own picture, and 108 the composite, before the
    first look. 62 screen readbacks, the first composition and every 75th after it, none differing.
  - *The reference.* 27 samples during the run, one per 64 free-heading frames, none differing. At the save the
    reference recomputed all 1,775 free-heading frames, all equal.
  - *The end.* Esc at tick 5,469. The mouse was released, then the session was certified, saved and verified: 1,832
    events, head `b28e42be62c4…`. Both the loop's output and the live block say `escape`.
  - *The beat, as counted.* 4,649 compositions against 5,470 ticks, 2,852 of them repeating the picture before them,
    and a span of 6. The loop fell behind the tick schedule. Nothing is concluded from that and nothing is changed
    because of it.
- **The owner's report of the run.** The look worked, and only horizontally. That is the scope this rung registered,
  not a fault in it. The camera carried from `urdr-oracle-2` turns in heading alone, the session's look is a change
  of heading, and the window hands the loop the horizontal count and nothing else. The 936 raw reports counted as
  `still` are the movements with no horizontal part: read, counted and not used. Looking up and down is not built.
  No frozen oracle holds a camera that pitches, so there is nothing yet to hold such a renderer to; as with the
  turning camera (VIEW-YAW-0), it would be earned in Urðr first. Whether it goes on the route is the owner's to rule.
- **The host's session replays here.** Read from the owner's folder, the saved file is verified by the workshop built
  in the container: its reference recomputed all 1,775 free-heading frames and reached head `b28e42be62c4…`. Those
  witnesses were made by the production tread on the owner's Windows host and reproduced by the reference kernel on
  Linux.
- **Sealed.** The owner pushed the host note and the declaration (`47fd54d`), then sealed the session on his host:
  `shell/attest/livesession-DANIELDILLBERG-b28e42be62c4.json` (`fcf48b2`). The record cites LIVE-SESSION-0,
  LIVE-INPUT-0, MOUSE-LOOK-0, SIM-TICK-0 and SIM-TICK-0a. Its reading: 1,832 events, 14 moves, 1,761 looks, 1,775
  frames at free headings recomputed by the reference before the save, ended by escape, run under the tick source
  with 1,761 looks. The workshop built on the host verified the saved file there, as the one built here did.

**Against the eight points, for the second run.**

| # | The point | The second run |
|---|---|---|
| 1 | A real mouse produces real look events | Shown: 13,931 raw reports, 1,761 looks. |
| 2 | A focus loss produces no session event | Shown: the window left the foreground and the log holds no event of any kind for it, and none with a tick inside the stretch. |
| 3 | Returning focus recaptures | Shown: captured twice, and looks follow the return. |
| 4 | Esc releases before the save | Shown: the release is printed before the certification and the save; ended `escape`. |
| 5 | The saved session certifies completely | Shown: 1,775 of 1,775 free-heading frames equal under the reference, on the host and again in the container. |
| 6 | No overlay at a free heading | Shown at the readbacks: the screen is the session's picture alone, one composition in 75. |
| 7 | The live render and the reference agree | Shown: 27 samples during the run and all 1,775 frames at the save. |
| 8 | No latency claim | None is made. |

**What the second run does not decide.** Why the first run had no mouse report. In the second run every raw input
message was read (unread 0), under the amended read. The section records the size of a read that fails and not of one
that succeeds, so the record cannot say whether the earlier read, which required an exact size, would have admitted
the same messages. Whether the mouse was moved in the first run is not in its record either.

**Grade.** DECLARED: the corrected wording, the rule for the end of a run, the observation's counters. ESTABLISHED
(gate, in the build container and on the owner's host): the two rows above, and MOUSE-LOOK-0's six under the amended
mock. MEASURED (the second host run; its session saved and verified there, verified again here, and sealed:
`livesession-DANIELDILLBERG-b28e42be62c4.json`): a real mouse making looks on the tick, the focus lost and regained with no session event, the session's picture on the
screen, the reference agreeing at every sample and every frame, the end recorded as `escape`. NOT_MEASURED: latency;
what a look costs phase by phase; why the loop fell behind the tick schedule; why the first run had no mouse report.

**does_not_show.** Why no mouse report reached the loop in the first run, or whether the mouse was moved in it. That
the changed read fixed anything: nothing shows the old read was what failed. That a span above 1 costs anything on
the screen, or how often the loop fell behind. That the section's own drop works on the host: Windows delivered
nothing to drop. That the screen showed the picture at every composition: one in 75 is read back. Anything about
looking up or down: vertical motion is counted and never used. Anything on another host or with another mouse.

**Falsifier.** `mouselook0a-ending` goes red if a run its Esc ended is recorded as closed, if the composition that
drains the Esc is presented, if an input is lost or applied twice at the end, or if the sealer says a session with no
look looked. `mouselook-fence` goes red if a raw input message is not counted before it is read, or if anything but a
captured relative horizontal count reaches the loop. On the host: an observation that does not add up
(`raw_messages` is not the sum of `unread`, `absolute`, `still`, `reports` and `dropped`).

## ADMIT-0 — the admission seam: a proposal in VRDNP1 recognized or refused, and admitted as one ordinary edit with its envelope beside it (preregistered and built; the gate passes on the host, and the first admission was made and sealed there)

**Why.** The owner declared that the gate certifies the program and that content is admitted, not gated, and ruled
that this is what the route builds towards. ADMIT-0 is the first rung of it: the seam through which a change to the
world enters the one session from bytes nobody trusts. In his words, *the gate certifies the machine; ADMIT admits
the world's changes.* The courts, the research, his review and the registration are recorded in
[`docs/ROADMAP.md`](../docs/ROADMAP.md).

**What it registers** (`bdd38593…`, registered and pushed before any of this was built).

- **The language.** `VRDNP1`: exactly eight lines, each ended by one LF. `VRDNP1`; `renderer=`, `bearing=`,
  `parent=` and `proposal=`, each with 64 lower-case hex characters; `op=` open, close or paint; `target=`; `value=`.
  327 to 337 bytes. Each typed proposal has one byte sequence, and its digest is the SHA-256 of those bytes.
- **The checks, in order.** `ADMIT-IO`, `ADMIT-SIZE`, `ADMIT-PARSE`, `ADMIT-RANGE`, `ADMIT-PROGRAM`, the session
  loader's own refusals, `ADMIT-SESSION`, `ADMIT-ANCHOR`, `ADMIT-DUPLICATE`, `ADMIT-CAPABILITY`, `ADMIT-AUTHORITY`.
- **The event.** The edit a key would make, with the head that edit gives, and an envelope beside it that is never
  folded.
- **One recognizer.** The proposal's bytes are read by one function of the shell. The workshop and the sealer never
  read the language.

**What was built.**

- **`shell/admit.rs`.** The recognizer (`recognize`) and the emission (`emit`), which is its inverse on every
  accepted input. The grant, read from `--allow`, `--cells` and `--classes`. The run: the proposal's bytes read
  (never past byte 338), recognized, the identities compared with this shell's, the saved session loaded once, then
  the anchor, the id, the grant and the authority, in that order.
- **The authority is the session's own.** The admitted edit is appended to the loaded session in memory by the
  session's own push, with its validation, its replay and its fold, before anything is written. There is no second
  copy of the edit's rules in the seam. A proposal the session refuses, or one that leaves W and M as they are, is
  refused with nothing on the disk.
- **The run opens after the checks.** `go_admitted` (in `shell/livesession.rs`) creates the run's directory and
  journal with the parent's events, appends the admitted event's record, and hands over to `finish`, the seal every
  live session uses: certified by the reference, written to a temporary file, flushed, moved into place, read back
  and verified. The parent's file is never opened for writing.
- **The envelope.** `playback::Admit`: the language, the proposer's id, the digest, the renderer and bearing
  identities, the parent head, the resulting head and the grant's line. The session fills in the two heads itself, at
  the fold, so nothing can hand it a head. It is written beside the event in the journal record and the saved item,
  with its members in one order, and the loader gives it back to the event when it replays.
- **Three checks of an envelope, none of them a parser of the language.** The shell's loader, the workshop's
  `sessionwalk verify` and `verify/livesession.py` each take the envelope as typed values of the saved form and check
  the same things: eight text members, the language's name, 64 lower-case hex where an id, a digest, an identity or a
  head goes, the grant's line, on an edit, the head before the event and the head after it, no proposal id twice.
- **The commands.** `shell admit`; `shell admit-anchor`, which prints the four lines a proposal for a session begins
  with and reads only; `shell admit-selftest`, the same run with a death point named, or the reader court in process.
  `shell admit` takes no plant.
- **The sealer.** A session with admitted edits is sealed citing ADMIT-0, with the count, and with the digest's limit
  among the readings it forbids. A session with no envelope is read, cited and sealed as before.

**What the gate holds (9 rows, 218 in all).**

| Row | What it holds |
|---|---|
| `admit-preregistered` | The entry is the registered one, its clauses present; the shell's constants are the registered ones; the registered worked example is a proposal of 328 bytes with the registered digest. |
| `admit-reader` | The reader court. All 329 proper prefixes of a valid proposal and 42 named cases given to `shell admit` each end in their registered refusal: exit 2, one record, one ledger line, no panic, nothing left under the sessions root, the parent as it was. In process, every single-byte substitution, deletion and insertion of three valid proposals (513,792 mutants) is refused or is a proposal emitted byte for byte. |
| `admit-single` | The single-parser court. A recognizer written apart in Python inside the gate, a test oracle, gives the registered refusal and line on the 42 cases and agrees with the shell on each of them, on every prefix and on all 513,792 mutants (equal counts and equal digests of the verdicts). By source: one function reads the bytes; the workshop and the sealer hold the language's name and nothing else of it; the oracle is used by these rows only. |
| `admit-anchor` | A stale parent refused `ADMIT-ANCHOR` with both heads named; another renderer or bearing identity refused `ADMIT-PROGRAM`, before the anchor is looked at; a journal refused `ADMIT-SESSION`; `admit-anchor` prints exactly the four leading lines. |
| `admit-capability` | No grant, an operation kind not granted, no cells named, a rectangle one cell short, a class not granted: `ADMIT-CAPABILITY`. Inside the grant, a cell outside the level, a border cell opened, a closed cell closed and an open cell opened: `ADMIT-AUTHORITY`. Eight malformed command lines are usage refusals. The smallest covering grant admits, and is what the envelope records. |
| `admit-idempotent` | The same bytes offered to the child are stale; the same id re-anchored is `ADMIT-DUPLICATE`, also two admissions later; the same edit under a new id is admitted; the same bytes admitted again to the untouched parent give a second file with the first child's data block byte for byte. |
| `admit-crash` | The run ended with exit 70 at eight points. The parent's bytes never change. After the first three nothing exists. After the journal is opened, and after the admitted record is torn half-way, the journal loads to exactly the parent's head. After the record is flushed, the temporary file written, and the saved file moved into place, what is left loads to exactly the child's head with the envelope the clean run wrote. No journal record holds the event without its envelope. |
| `admit-replay` | An admitted open, close and paint each have the head, content, spec and witness of the same edit made by a key from the same parent, differing by the envelope alone. The workshop verifies each child without the shell. The sealer cites ADMIT-0 and counts the admitted edits. Sixteen resealed forgeries of an envelope are each refused by the shell, the workshop and the sealer. A continuation by keys keeps the admitted item byte for byte, and one by the workshop keeps the envelope. |
| `admit-fence` | `shell/admit.rs` spawns nothing, connects to nothing, reads no clock and nothing under `verify/`. The checks are in the registered order on one load. The run is reached by `admit` and `admit-selftest` alone. The envelope is filled after the fold in both edit paths. The saved form's JSON reader is byte-identical in its three files and untouched. Kernel sources, `shell/present.rs`, `shell/simtick.rs` and the LATENCY-0 prefix are unchanged. |

**Found while building.**

- **Thirty-nine mutations: thirty-seven caught at once, two after the rows were strengthened.** Each was applied to a
  scratch copy and is a defect that leaves the program running. In the recognizer: bytes after the eighth line
  accepted, a leading zero accepted, upper-case hex accepted, a range refusal returned early, the size not bounded
  first, a refusal naming the wrong line, an emission that is not the bytes, the reader court skipping its
  insertions, a coordinate bound moved by one. In the checks: the digest taken of re-emitted bytes, a stale anchor
  admitted, the bearing identity not checked, a repeated id admitted, duplicates compared by digest, the grant not
  consulted, the rectangle or the classes not looked at, a proposal that changes nothing admitted, a journal
  admitted to, the program checked after the anchor. In the envelope: folded into the head, dropped by the loader,
  its parent unchecked, its id allowed twice, allowed on a move, its digest taken of something else, put on a key's
  own edit, left out of the journal record, dropped by the workshop. In the verifiers: the workshop not checking the
  resulting head or the member count, the sealer not checking the language or the grant's line, or not citing this
  entry. In the run: a refused admission leaving a directory, `shell admit` taking a plant, a process spawned, a
  death point moved, a torn record written whole.
- **The two that survived showed gaps in the rows, not in the seam.** A range refusal returned before the rest of the
  bytes were recognized passed, because the corpus had a range fault followed by a fault on line 8, which the
  recognizer reaches before it looks at any domain, and nothing with a range fault followed by a byte after the last
  line. That case was added. And a loader that let an envelope sit on a move passed, because the forged envelope
  still named the heads of the edit it was taken from and was refused for those. A forgery naming the move's own
  heads was added, so that being on a move is the only thing wrong with it. Both mutations are caught now.
- **Two refusals have a second line behind them.** With the seam's duplicate check removed, the admission is still
  refused: at the save, by the loader's check of the file it has just written. With the envelope folded into the
  head, the save refuses because the stored head is no longer the fold of the witnesses.
- **The two recognizers agreed at the first comparison.** The shell's recognizer scans bytes; the gate's oracle
  splits lines and matches regular expressions. Run against each other over all 513,792 single-byte mutants they
  gave the same verdicts. What needed correcting was the corpus: three of its cases as first written (a repeated
  identity line, a paint with a nine-digit colour, and a colour out of range followed by a ninth line) are longer
  than 337 bytes, so by the registered order they are size refusals and never reach the parser. They stay in the
  corpus as that. The registration's "repeated line" is held by repeating the short `op=` line, which fits. One of
  the three bases is a proposal of the greatest length, so that every insertion into it is a size refusal and both
  recognizers are compared on that precedence too.
- **No pin of an earlier rung moved.** The envelope is taken beside the fold with the fold's statement left as it
  was, so the fences that pin that statement pass unchanged. The JSON reader's text is untouched in all three files.
- **The workshop carries an envelope when it continues a session.** Its own verbs rewrite a session-walk in the
  workshop's format. An envelope is kept as read and written back beside its event, so a workshop continuation does
  not drop it. The row checks that.
- **A refused admission is one line in each log and nothing else.** The rows use a sessions root of their own, so
  "leaves nothing" is a listing of that root before and after, and not a search.
- **The Windows build is type-checked here and not run.** The seam has no window code; `shell/win32.rs` is not
  touched.

**What the host run was for.** `shell admit` is windowless and is the same program on the host as on the gate. The
host witness is one admission to a session sealed there: the proposal recognized, the child saved and verified by
the shell, verified by the workshop built there, and sealed by `verify/livesession.py` citing this entry. This was
written before the run.

**On the owner's host (2026-10-03): the gate, and the first admission.** The owner applied the build, with the two
docs commits before it, ran the gate, pushed (`8e3f13b`), admitted one proposal to a session sealed on that host,
offered it a second time, sealed the result (`3f3e0e2`) and pushed.

- **The gate.** `GATE PASSED`, 218 rows, none failed and none skipped, rowset `0b423b279a40c85c`: the same rows and
  the same rowset as here. The nine `admit-*` rows ran there on Windows, with the shell built there.
- **The parent.** The session of the second `look-window` run, sealed there earlier: 1,832 events, head
  `b28e42be62c4…`, ending at a free heading at cell 23,27.
- **The proposal.** 329 bytes of `VRDNP1`, anchored to that head, opening the cell 20,27, two cells ahead of where the
  session ended. Its bytes were produced in the build container by a short script, from the four lines `shell
  admit-anchor` printed for a copy of the session. No model generated it from a prompt, and nothing is claimed about
  one. The grant on the command line: open, cells 1,1 to 46,30.
- **The admission.** Recognized (proposal `8e54172b6f72…`, digest `f15fbb474fa4…`). Admitted as `cell:20,27,.`,
  head `b28e42be62c4…` to `a0861e0e837b…`. All 1,775 free-heading frames of the log recomputed by the reference
  before the save, all equal. Saved and verified by the shell: 1,833 events, run `1a1039bef21-63c0`.
- **The head was written down before the run.** The same bytes were admitted here first, to a copy of the session
  read from the owner's folder, and gave the head `a0861e0e837b5593…`. The host gave the same head. Its saved data
  block is the one saved here, byte for byte (375,430 bytes), across two machines and two operating systems. The
  envelope holds nothing of the run that made it.
- **The same bytes, offered again.** To the child: `ADMIT-ANCHOR`, naming both heads, no rebase. One record in the
  host's refusal log, with both heads in its context; one line in its run ledger, ended 2 with one refusal. No run
  directory: the sessions folder's last entry is still the child's.
- **The parent is as it was.** Its bytes on the host hash to what the child's lineage recorded when it loaded them
  (`6d60d51c…`).
- **The envelope.** The language, the proposer's id, the digest (equal to the SHA-256 of the proposal file), this
  build's renderer and bearing identities, the two heads, and the grant's line `allow=open cells=1,1,46,30
  classes=-`. It is in the journal's last record and in the saved item.
- **Sealed.** `shell/attest/livesession-DANIELDILLBERG-a0861e0e837b.json`, citing LIVE-SESSION-0 and ADMIT-0. Its
  reading: 1,833 events, 14 moves, 1 edit, 1,761 looks, one of the edits admitted through this seam, ended by
  admission, a continuation of the session whose head is `b28e42be62c4…`. The workshop built on the host verified
  the saved file there and counted one envelope; the workshop built here verifies the same file to the same head.
- **What the run ledger says of the two runs.** 44.2 seconds between the start and the end of the admission, and
  16.3 seconds for the refused one, by the ledger's wall-clock stamps. One run each. It is recorded and nothing is
  claimed from it. It is what the registered limit says: an admission loads, certifies and reads back the whole
  session, and a stale proposal is refused only after the session it names has been loaded and replayed.

**Grade.** DECLARED: the registered conditions. ESTABLISHED (by rows, on every gate, here and on the host): the
reader, single-parser, anchor, capability, idempotency, crash and replay courts over the gate's own proposals and
the session's mock, and the fence. MEASURED (on the host, sealed): one admission to a session sealed there, its
head the one computed here beforehand and its data block byte-identical to the one saved here; the same bytes
refused as stale against the child, leaving nothing. OBSERVED: the run ledger's two intervals. NOT_MEASURED: what an
admission costs; durability under power loss; anything about a model.

**does_not_show.** That a model can write a proposal worth admitting, or any safety property of a system that
includes a model: no model is in the tree and the gate wrote every proposal here. That a later verifier can
recompute an envelope's digest: the proposal's bytes are not kept, and the envelope is the admitting shell's record
under a seal that is a hash and not a signature. Durability after a power loss: the crash court ends the process at
eight registered points and nothing else. Agreement of the two recognizers beyond the corpus and the single-byte
neighbourhood of three proposals. Anything about the saved form's JSON reader, which the seam reads the session
through and which `READER-COURT-0` hardens after this rung. Anything about a vocabulary beyond a cell opened or
closed and a tile class painted.

**Falsifier.** `admit-reader` goes red if any byte sequence outside the language is recognized, if a recognized one
has a second spelling, or if a refusal panics, leaves a directory or changes the parent. `admit-single` goes red if
the shell and the oracle differ on one verdict, or if a second reader of the language appears. `admit-anchor` goes
red if a stale parent or another identity is admitted. `admit-capability` goes red if anything outside the grant is
admitted, or a proposal that changes nothing is. `admit-idempotent` goes red if a repeated id is admitted or the
same bytes give a different world. `admit-crash` goes red if what a dead run left loads to anything but the
parent's head or the child's, or if an event and its envelope are ever apart. `admit-replay` goes red if an
admitted event's head is not the key-made edit's, if a forged envelope passes any of the three verifiers, or if a
continuation drops an envelope. `admit-fence` goes red if the seam reaches a process, a socket, the gate or the
JSON reader's text.

## READER-COURT-0 — the saved form is one bounded language, and every reader gives one verdict (preregistered `f53017cd` and built; the gate passes here; the first host run read 225 of 226, the one red a planted file written CR LF on Windows, fixed; the second host run passes, 226 rows, and is pushed)

**Why.** ADMIT-0 made a new language with one reader. The old language, the JSON the tree saves and reads back, has
four Rust parsers (one text copied into `shell/playback.rs`, `workshop/sessionwalk.rs` and `workshop/session.rs`,
and a different one in `workshop/edit.rs`), four Python readers on `json.load`, and three writers with three
layouts. On 2026-10-03 the Rust reader and Python's were given 19 hostile inputs and differed on 12; on three the
Rust reader returned no verdict (ADMIT-0's section, and [`docs/ROADMAP.md`](../docs/ROADMAP.md)). ADMIT-0 reads the
session through that reader. This rung is next by the owner's order, and its two courts (2026-10-04) are recorded in
the roadmap.

**The method (`f53017cd`), as registered.**

- **The language** is what the tree's registered writers are permitted to emit, and nothing wider. A document is
  one object followed by exactly one LF; a journal record's payload is one object and nothing else. Between tokens
  there may be spaces and LFs only. No name occurs twice in an object. An integer is `0`, or an optional `-` and a
  digit 1–9 followed by digits, within signed 64 bits: no leading zero, no minus zero, no fraction, no exponent. A
  string is well-formed UTF-8 with one spelling: `\"` `\\` `\b` `\f` `\n` `\r` `\t`, and `\u00XX` in lower-case hex for
  the other characters below U+0020 and for nothing else. Strict RFC 8259 and canonical bytes are both rejected.
- **Depth.** Objects and arrays nest at most seven deep. The count is of the objects and arrays open at once, the
  root object counted as the first; a string, an integer, `true`, `false` or `null` opens no level.
- **The verdict** on any bytes is ACCEPTED with a typed value (compared as the sha256 of its RECORD-0 canonical
  JSON), or REFUSED with a code and a byte offset. The codes: `READER-TRUNCATED`, `READER-TRAILING`, `READER-DEPTH`,
  `READER-DUPLICATE`, `READER-STRING`, `READER-NUMBER`, `READER-STRUCTURE`. The offset is the first byte at which the
  input stops being the beginning of any document of the language, or the input's length if it ended where one could
  still continue. It is a property of the language and the bytes; no reader owns it.
- **One Rust reader**, `kernel/savedform.rs`, beside `formats.rs`, included by path by the shell and by the
  workshop's `sessionwalk`, `session` and `edit`. The four parsers are removed. The file owns reading the language
  and its one string spelling and knows nothing of the shell, the workshop, a session, admission, a renderer, a file
  or a process. It is not in either renderer identity.
- **An independent Python reader**, `verify/savedform.py`, with no `json.loads` underneath, used by the sealer
  (`verify/livesession.py`), `verify/seal_sessionwalk.py`, `verify/seal_session.py` and `verify/envelope.py`'s read.
  Neither reader is right because the other agrees.
- **Writers refuse beyond it.** Every writer of the saved form gives its bytes to the reader before it writes them.
- **The court.** 45 boundary cases, each with its verdict written into the entry. Every single-byte substitution,
  deletion and insertion of three registered documents (135, 101 and 81 bytes, which between them use every kind of
  value and every escape), both readers giving the same verdict on every mutant. On every committed record, the
  host's records when present, and the sessions, journals and checkpoints the gate makes: acceptance by both readers
  to the same typed value, and the registered boundary mutations at every place they fit when the document is at
  most 65,536 bytes, and at the first and the last place of each kind when it is larger, the expected code and
  offset computed from the place and not by a reader. A hostile document given to each real command is refused
  there with the same code and offset.
- **Rows:** `readercourt-preregistered`, `-language`, `-agree`, `-corpus`, `-writers`, `-commands`, `-single`,
  `-fence`, under *What was built* below.

**The three depths are one number.** The owner's check before the push: the deepest a writer emits, the deepest the
readers accept and the deepest the court tests must be the same, and the court must show the edge from both sides.

| | |
|---|---|
| A, the deepest a registered writer emits | 7: sixteen of the host's sealed measurement records (FRAME-SPLIT-0's is root, data, arms, production, split, phases_us, strips). OBSERVED over the 49 records and sessions present on 2026-10-04; none is deeper. |
| B, the deepest the readers accept | 7, by the registered language. |
| C, the deepest the court tests | 7 accepted, with 6 accepted below it and 8 refused above it. |
| six levels, `{"a":[[[[[1]]]]]}` and LF | accepted |
| seven levels, `{"a":[[[[[[1]]]]]]}` and LF | accepted |
| eight levels, `{"a":[[[[[[[1]]]]]]]}` and LF | `READER-DEPTH 11`: the bracket at offset 11 would open the eighth level |

**A count corrected.** The record of 2026-10-04 said the deepest shape among the files was 6 levels. That was the
deepest among the session files; the count had missed the measurement records, where it is 7. It was found by
counting again while the entry was drafted. The owner's ruling it had prompted (bounds come from the writers, not
from the files) is untouched by the number, and the entry registers seven as an observation of the records present
and not as a proof about every input a writer could be given.

**The registration's history, kept visible.** The entry was first drafted with hash `0ecbec22`. That draft was
applied on the owner's host as patch 0110 and gated there: GATE PASSED, rowset `0b423b279a40c85c`, 218 rows, 0 fail,
0 skipped (a registration adds no row). It was not pushed. The owner reviewed it and locked it, with one condition
before the push: *make the depth convention explicit in the registered text if it isn't already*, and have the
court show six, seven and eight. Checked against the draft: the convention was there ("the root object counted as
the first"), and so were seven accepted and eight refused at offset 11. Six accepted was not. The entry was
therefore changed while its commit was still unpushed, which the rules allow, and its hash is now `f53017cd`. After
the push it changes only by an amendment with its own hash. What differs between the draft and the registration:

1. A boundary case added: six levels, accepted. The court now holds 45 cases.
2. The depth convention spelled out (what is counted, what opens no level), and the three depths named as one
   number.
3. `verify/envelope.py`'s write, handed seven levels, writes them (the draft already registered that it refuses
   the eighth).
4. A limit added: the JSON under `oracle/` that Urðr's tags fix is frozen evidence, read by Python alone, not the
   saved form, never rewritten and not covered. All three of those files lie outside the language (one has no final
   LF, two write a character above U+007F as a `\u` escape).
5. A condition added: a forgery an earlier row makes that lay outside the language (a tampered record written
   without its final LF is one) is written inside it, so it is still refused for its own row's reason and not for
   this rung's; each one rewritten is listed. Its failure is registered too.
6. A limit added: that seven is the deepest a writer emits is an observation, not a proof.

Items 4 and 5 came from reading every JSON file two gate passes leave behind (323 files; 297 inside the language,
the rest the frozen oracle files and earlier rows' forgeries) before the push. They narrow the claim and add an
obligation to the build. They change no ruling.

**The owner's review of the draft (2026-10-04).** Eight points, each locked.

1. **Depth 7.** Lock, provided the counting convention is explicit.
2. **Writers check their own bytes.** Lock. No circular authority: the format's definition stands above both, the
   reader is independent of the writers, and a writer is checked against the reader.
3. **`kernel/savedform.rs`.** Lock. A shared file beside the kernel's formats; not in the renderer's identity.
4. **One string spelling.** Lock.
5. **Whitespace is spaces and LF.** Lock.
6. **Large files: the first and the last place of each kind.** Lock. Deterministic and documented.
7. **The `--out` raws, the two logs and the registry are left out.** Lock.
8. **ADMIT-0's pin of the old reader moves here.** Lock. *Historical pin ≠ current implementation.* History is not
   rewritten: ADMIT-0's registered entry stays as it is, and this rung lists the pin it moves.

One caveat on evidence: the prototype's result stays *outside the gate, a compatibility measurement*, and is not to
be read as "therefore equivalent to Python". His ruling: ***0110: LOCK / PUSH. No redesign.***

**Outside the gate (OBSERVED, a compatibility measurement).** A prototype of the reader, written before the
registration, accepts all 52 documents then available (every committed record, the host's records and saved
sessions, the registry) and 4,298 journal payloads, each to the typed value `json.loads` gives. That shows the
tree's existing files lie inside the registered language. It does not show the reader is equivalent to Python's
(it is registered to be stricter), and no gate row rests on it.

**On the host (DANIELDILLBERG).** `git status` read one commit ahead of `origin/main`: the draft. It was dropped
with `git reset --hard f504829`. The registration (0110, `f53017cd`) and the documents (0111) were applied in that
order, and the gate passed: GATE PASSED, rowset `0b423b279a40c85c`, 218 rows, 0 fail, 0 skipped, the same rowset
as in the container. Pushed, `f504829..25b5c17`. The draft was never public. The entry is, and from here it
changes only by an amendment with its own hash.

**What was built.** The owner's word after the registration was pushed: *take the next.*

- **`kernel/savedform.rs`, the one Rust reader.** A typed value, or a code and a byte offset. It reads with a stack
  it keeps itself, so no input can exhaust the machine's. It opens no file, prints nothing, uses the standard map
  and nothing else, and names nothing of who reads it. Its `spell` is the one spelling. It is included by path, once
  each, by the shell and by the workshop's `sessionwalk`, `session` and `edit`.
- **The four parsers are gone.** About 840 lines came out of `shell/playback.rs`, `workshop/sessionwalk.rs`,
  `workshop/session.rs` and `workshop/edit.rs`. Each loader now refuses with the reader's own line, so a refusal
  names the code and the offset: `SESSIONWALK-INVALID-SESSION: READER-NUMBER 3714`.
- **`verify/savedform.py`, the Python reader.** Written apart, with no `json.load` or `json.loads` beneath it. The
  sealer, the two session sealers and the envelope read through it and through nothing else.
- **Writers check first.** The shell's saved session (inside `write_saved`), each journal record's payload, the
  checkpoint's line, the workshop's three document writers, and `verify/envelope.py`'s write, which also holds that
  every name is a string and that the bytes read back to the record. A refusal writes nothing.
- **One spelling.** The workshop's three tools and the shell's saved-session writer spell every string through
  `savedform::spell`. The workshop's own spelling of backspace and form feed is gone.
- **The court command.** `shell form-verdict`, `form-court`, `form-splice` and `form-spell` ask the Rust reader
  questions without a session, a record or a window. `python verify/savedform.py --splice` is the same splice court
  for the Python reader. Each reads every mutant from its first byte.

| Row | What it holds, and what it read on this gate |
|---|---|
| `readercourt-preregistered` | The entry is locked, and the gate's 45 cases, three documents, seven codes and depth are the registered ones, verdict for verdict. |
| `readercourt-language` | Each reader gives the registered verdict on each of the 45 cases: 9 accepted to one typed value, 36 refused at the registered offset. Six levels and seven are accepted; the bracket at offset 11 is refused. |
| `readercourt-agree` | Every single-byte substitution, deletion and insertion of D1, D2 and D3: 163,072 mutants, the same verdict from both readers on every one (21,202 accepted to the same typed value; refused: STRUCTURE 88,521, STRING 49,539, NUMBER 2,210, TRAILING 1,332, TRUNCATED 230, DEPTH 24, DUPLICATE 14). |
| `readercourt-corpus` | 6 committed records and 128 things the gate makes (three saved sessions, their journals' payloads, a checkpoint's line, the workshop's three documents) are accepted by both readers to one typed value. The registered boundary mutations, placed by a lexer that is neither reader, 43,925 of them, each get from both readers the code and the offset their place gives. With the host's 33 records present: 181,376 mutants, two inputs over 65,536 bytes taking the first and the last place of each kind. |
| `readercourt-writers` | Every registered writer's bytes are accepted: three layouts, one language. The shared spelling and Python's give the same bytes for every character below U+0080 and for raw multi-byte characters (139 texts). The envelope's write refuses an out-of-range integer, an eighth level, a fraction and a name that is not a string, writing nothing, and writes seven levels. A shell planted to save an out-of-range integer, an eighth level or a repeated name refuses the save and leaves only its journal. By source, each writer checks before it writes. |
| `readercourt-commands` | A hostile document is refused by each real command, naming the same code and offset: a saved session with a fault inside and its seal recomputed, by `shell playback`, the shell's loader, `sessionwalk verify` and the sealer; documents with each of the seven codes by `shell playback`, `sessionwalk verify`, `session verify` and `edit check`; records by `envelope.read`. 55 refusals, none a panic. Each of the 19 inputs of 2026-10-03 has one verdict from both readers and from every command. |
| `readercourt-single` | By source: `kernel/savedform.rs` is the only JSON reader under `shell/`, `workshop/` and `kernel/`, included by path once per program; no Python tool calls `json.load` or `json.loads` on a saved-form document (checked on the syntax tree, so a docstring is not a call); `verify/savedform.py` calls neither. |
| `readercourt-fence` | The reader knows the language and nothing else; the renderer and bearing identities are what they were (`629ae5c7`, `2d1a2643`); `shell/admit.rs` is untouched; both readers are pinned; the old parser is gone; the LATENCY-0 prefix is intact; each of the eight records of sessions sealed before this rung, when present, is read to the typed value it had; and no earlier row's forgery was refused for its form. |

The gate reads 226 rows, rowset `39e5874a7127cfa4`.

**The watch.** The gate now watches every command it runs, and every read it makes itself, for a refusal by the
saved form's reader. `readercourt-fence` goes red if any row before this rung's own provoked one. It is how the
registered condition on earlier forgeries is held on every gate and not only on the day of the build.

**Forgeries of earlier rows, rewritten inside the language (listed, as registered).** Each was written before with
the json module's defaults: no final LF, and a `\u` escape for any character above U+007F. Each is now written by one
helper, `write_form`, and is refused for its own row's reason.

1. The tampered edit records (`tampered()`): `workshop-stale`, `workshop-projection`, `workshop-camera`, and the two
   plants of `records-twins`.
2. `workshop1-tamper`: the session with a changed entry.
3. `sessionwalk-tamper`: the session-walk with a changed move.
4. `shell-playback-order`: the reordered log.
5. `shell-playback-tamper`: the tampered move and the truncated log.
6. `shell-playback-sealed-input`: the artifact that is not a session. This row stayed green with the strict reader,
   for the wrong reason; the watch found it, not a red row.

**Pins moved on purpose (listed, as registered).** One.

- `admit-fence` held the old JSON reader's text byte-identical in three files (`3b6ceb22`). That reader is removed.
  The pin moved here with it: `readercourt-fence` pins both new readers (`kernel/savedform.rs` `a6c6fb66`,
  `verify/savedform.py` `f33ee6fb`), and `admit-fence` now pins `shell/admit.rs` itself (`99366fea`). ADMIT-0's registered
  entry is as it was: a historical pin is not the current implementation.

No other pin moved. Where an earlier fence pins a call's text or a count in a file this rung edits, the edit was
shaped to leave it standing: the save's check sits inside `write_saved` and not in `finish`, so LIVE-SESSION-0's
fence still finds the save call it pins and still counts three refusals there.

**What the build found.**

- **The court caught its author first.** A fast path in the Python reader for small integers admitted `-0`. The
  registered case *minus zero* and five mutants of the exhaustive court differed from the Rust reader at once. It
  was fixed before any row existed. The fast paths (a plain string, an integer of at most 18 digits) took the
  reader from about 1 MB/s to about 12 MB/s here; every refusal still comes from the exact path.
- **Nine rows had forgeries outside the language.** Eight went red against the strict reader. The ninth did not.
- **The mutation test (off the gate).** 55 planted defects: 25 in the Rust reader, 11 in the Python reader, 19 in
  the writers, the loaders, the tools and the gate. Every one is caught, 54 by a row that exercises behaviour or
  reads source, one (a forgery put back outside the form) by the watch. On the first run five showed as surviving
  and none was a gap in a row: four were mutants written so that they changed nothing (a check wrapped in a pattern
  that still fired, a copy that was never used), and one needed the earlier row run beside the fence. Rewritten so
  that they do change the program, all are caught.

**Off the gate, here (OBSERVED).** With the host's 33 records copied in, the gate passes with the same 226 rows.
The eight sessions sealed on the host before this rung were replayed by `sessionwalk verify` built from this tree,
and sealed again by the new sealer from the saved files: each record's data is the same as the one sealed on the
host. The provenance differs in the Python version and the operating system, as it must. On the owner's host both
are his to run.

**On the host (DANIELDILLBERG), the first run.** 0113 and 0114 were applied and the gate read 226 rows, rowset
`39e5874a7127cfa4`, 1 fail, 0 skipped. The red row was `readercourt-fence`: *a forgery of an earlier row was refused
by the saved form's reader and not for the row's own reason: shell-playback-sealed-input.* Every other row passed
there, the corpus with the host's records among them.

- **The cause.** That row plants a file that is not a session. The build rewrote the plant to end in a line feed and
  left it opened in text mode. On Windows the final LF was written as CR LF. The language holds no CR before the
  final LF, so the reader refused the file (`READER-TRAILING 34`, reproduced here on the same bytes) before the
  row's own rule was reached. On Linux the same code wrote LF, so the three passes here were green.
- **What caught it.** Not the row, which stayed green on the host as it had before the build. The watch did, on its
  first host run. The reader's verdict was the correct one for the bytes it was given.
- **The fix.** The plant is written as bytes, so its line ending is LF on every host. One line of the gate; no
  rule, no reader and no registered entry is changed. The owner's reading: *the host found a real registration
  defect, the fix is byte-level, and the reason is now understood.*
- **What it says about the method.** The gate here cannot see what another platform does to a file. The mutation
  test had this very defect as a planted case (a forgery put back outside the form) and the watch caught it there;
  the real instance differed by a line ending only the host produces. Three green passes here were three samples
  of one platform.

**On the host, the second run (2026-10-05).** The fix (0115) and its record (0116) were applied and the gate read
`GATE PASSED`, rowset `39e5874a7127cfa4`, 226 rows / 0 fail / 0 skipped: `shell-playback-sealed-input` green and
`readercourt-fence` green. The owner pushed `b847810..b077eef`. The eight sessions sealed on the host before this
rung were not sealed again there, or it was not reported; that check stands as it was made here.

**Grade.** DECLARED: the registered conditions, and the owner's eight locks. ESTABLISHED (gate, here): the eight
rows. MEASURED (host): 225 of 226 rows on the first run, the fence's red a true finding; 226 of 226 on the second,
with the fix. OBSERVED (here, off the gate): the census, the depth count, the prototype's result, the mutation
test, the gate with the host's records copied in, the eight sessions sealed again to the same data. NOT_MEASURED:
how long the new rows take on the host, and the eight sessions sealed again there.

**does_not_show.** That the language is right: it is one author's grammar, and what stands against a shared mistake
is the registered cases, offsets computed from the place of a mutation, and the writers' own output. Anything about
bytes outside the three small documents and the registered mutations. That a writer's check runs, beyond the
shell's save: for the journal, the checkpoint and the workshop's writers the check is held by source, which shows
it is written before the write and not that it fires. Anything about a document's meaning: the loaders are as they
were. Anything about the raws, the two logs, the registry or the frozen JSON under `oracle/`.

**Falsifier.** `readercourt-language` goes red if either reader gives another verdict on a registered case;
`readercourt-agree` if the two differ on any mutant or either leaves one without a verdict; `readercourt-corpus` if
a real file is refused or read to another value, or a boundary mutation gets another code or offset;
`readercourt-writers` if a writer writes bytes outside the language or writes before it checks;
`readercourt-commands` if a command accepts a hostile document, names another code or offset, or panics;
`readercourt-single` if a second reader or a `json.loads` remains; `readercourt-fence` if the shared file knows
anything but the language, a reader's text changes, an identity moves, or an earlier row's forgery is refused for
its form.

**The next question, reserved.** Whether DESIGN-EVENT-0 remains the next rung, or a design representation, a design
diff and constraints are promoted ahead of it. The owner: *I would not silently reorder that based on the 15-pivot
review. That deserves its own ruling.* The locked order stands until he rules.

*Ruled on 2026-10-06: DESIGN-EVENT-0 stays next and the design representation follows it. See DESIGN-EVENT-0 below.*

## REASON-COURT-0 — every refusal the gate requires, held to a registered reason (preregistered `337ab021`; heard on the host before the build; built: six rows, 232 in the gate; the gate passes here and on the host; pushed)

```
  a row's statement ───────────────►  the register  verify/reasons.json   ◄── the ledger entry pins its bytes
  "exit 2 and CHAIN-BROKEN in err"    expected:  a code  ·  REFUSE(any) with its reason  ·  a death (70)
                                      never filled from what a program prints
                                            │
  a child of the gate ends ≠ 0 ──► the watch ──► the code head of a line ──► a slot of its group
                                                 SESSIONWALK-CHAIN-BROKEN: the head…   (row · program · command)
                                                 └ framing ┘└── the code ──┘  text after the head is never read
```

**Where it came from.** READER-COURT-0's watch showed a row that had stayed green while its plant was refused for
its form and not for the row's own reason. A row that asks only for a refusal passes whatever refused. The owner
locked the idea and ruled it its own rung. The first court and its three rulings are in
[`docs/ROADMAP.md`](../docs/ROADMAP.md).

**The census (the rung's first operation; no row, program or document was changed to make it).** The gate as patch
0116 left it — `verify/verify.py`, sha256 `f6dde802…c14b`, 11,939 lines, 226 rows — was counted twice and netted a
third time:

- a **reading** of every line, in twelve windows under one rubric;
- an **extraction** from the syntax tree of every comparison of an exit status with a non-zero number and every
  handler of a refusal exception: 76 sites, all of them in the reading or among eight that require success;
- a **third net** over the gate's own failure texts that speak of accepting, refusing, a plant or a forgery: 59
  near-candidates, read one by one, none a refusal check.

| kind | statements | what it is | in the court |
|---|---:|---|---|
| refusal | 129 | a program must end non-zero, or a function must raise | held |
| refusal as data | 16 | a refusal reported in a trace, a verdict line or a returned list | held |
| second witness | 16 | a log record, a ledger line or the disk, for a refusal already judged | attached to its refusal |
| planted death | 4 | exit 70 and a named line | held |
| detection | 7 | a plant caught because a value moved; nothing refuses | outside |
| gate-self | 6 | one of the gate's own checks held to a plant | outside |
| agreement | 1 | two readers must agree; neither must refuse | outside |

190 statements were recorded; 11 are helper definitions, counted through their calls. The **145 refusal checks**
stand in 78 of the 226 rows. Beside them, 63 functions of the gate trust a line a program prints about its own
court (`court OK`, `selfcheck OK`); those courts were not opened.

**What the census showed (OBSERVED, of the gate as it stood).**

| of the 145 refusal checks | |
|---|---:|
| hold a named code | 103 |
| hold words of the diagnostic and no code | 8 |
| hold other evidence (nothing written, one new record, a count) | 12 |
| hold only that the subject refused | 22 |

- **21 of the 22 are the sealers under `verify/`.** They refuse in prose. Of 148 `raise Refuse(...)` only
  `drift.py`'s begin with a code, and the row that judges them does not read it.
- **Where the codes are named.** A ledger entry names 23 of the 83 codes the court holds; `RUNGS.md` names 15 more;
  45 were named nowhere but the program that prints them and the row that asks for them.
- **How a code was held.** 73 of the 103 looked for it anywhere in the output. `PRESENTEXACT-READBACK` is also found
  in `PRESENTEXACT-READBACK-STALE`; a verdict `CODE 12` is also found in `CODE 120`.
- **One code, several causes.** `INVALID-EDIT` answers six edits, `DIVERGED` four forgeries, and `records-twins`
  asks `ENVELOPE` of two different plants.
- **Exit status.** 74 statements require exit 2; 23 require only a non-zero ending.

**What each refusal says today (a listening pass, off the gate; OBSERVED, one run here).** The whole gate was run
with a listener that kept every child that did not end 0 and every sealer refusal. The gate read the same with it
on. It heard 1,103 endings (1,090 exit 2, 11 exit 70, 2 exit 1) and 74 sealer refusals, and no panic. Every refusal
of this tree's programs carried a code. Every sealer refusal was for the cause its row names (57 of 57 planted
records, by reading). Among what it could hear, no wrong-reason pass was found. It found one ending no statement
judges: `shell-build` runs `shell run`, receives exit 2, and drops the result. By the owner's ruling none of this
is where an expected value comes from.

**The courts (2026-10-05), after the census.** Four rulings, then two tightenings.

1. **The edge.** The court holds the 145 refusal checks, their 16 second witnesses and the 4 planted deaths. The
   deaths belong because they answer the same question from the other side: *does the program end with the
   registered reason rather than merely not pass?* Detections, gate-self checks, the agreement court and the
   programs' own courts are registered as outside, *otherwise REASON-COURT-0 becomes a general
   assertion-strengthening project rather than a reason court.*
2. **Where a code comes from: register here, with a witness.** *REASON-COURT-0 can register an already-existing
   requirement; it must not manufacture a new requirement.* Three sources: an earlier ledger entry; `RUNGS.md`, with
   its state pinned; the row's own requirement, first registered here, each with the text of the gate that requires
   it. *The implementation cannot be used to establish the expected code.* Amending some twenty earlier rungs was
   rejected.
3. **The sealers: `REFUSE(any)` with a condition, and no sealer changed.** The condition is that the plant is the
   registered mutation of a record the same row requires accepted. A plant that does not meet it is not silently
   downgraded.
4. **A table and a watch.** The table is the authority and is never filled from observed output. The watch is the
   completeness fence: *no non-zero ending may remain unclaimed.* The 145 statements are not rewritten.
5. **The code head (a correction of "first token").** The watch reads the leading run of code tokens on a line and
   never the text after it. The prefixes programs print (`SESSIONWALK-`, `SHELL-PLAYBACK-`) are *observed framing,
   not the reason contract*, and are not registered. The cases where a code stands in prose are named exceptions,
   held as their row holds them: *don't pretend the code-head grammar covers them.*
6. **One registered mutation.** A plant meets the condition when all its differences from its accepted twin are
   the registered primary mutation and the deterministic recomputation closure of that mutation. The others are
   registered `condition_status = NOT_MET`, `condition_debt = CODE | ACCEPTED_TWIN`: *a visible, finite debt rather
   than quietly weakening the court.*

**What is registered.** Entry `337ab021dc83f564fae619e8f7827bbfaf8219b42aef694cf19118aaa4336729`, and the register
it pins: `verify/reasons.json`, 199,090 bytes, sha256 `cf3f47e5…1d6b`, a document of the saved form.

| the register holds | |
|---|---|
| codes | 83, each with its source: 23 a ledger entry, 15 `RUNGS.md` (line cited), 45 first registered here |
| statements | 165 (145 + 16 + 4), each with what it expects and the gate's own text that requires it: 215 code requirements in 115 statements, every one with its literal and its lines |
| refusal checks | 103 expect a code; 42 expect `REFUSE(any)`, each with its reason |
| endings | 1,103 in 77 groups by row, program and command: 1,072 owe a code in a code head, 23 `REFUSE(any)`, 6 held only by their row, 2 unjudged |
| named exceptions | three statements, nine endings: the compiler's `error[E0502]`; the reader's verdict in the Python sealer's command line; the reader's verdict in parentheses after `LIVESESSION-FORM` |
| planted records | 57 behind the 21 sealer statements: 41 meet the condition (34 one field, 7 one field and its closure), 16 are debt; and 16 forged envelopes of `admit-replay`, 14 met and 2 debt |
| outside | 7 detections, 6 gate-self checks, 1 agreement court, 63 program-owned courts, by name |

The expected code of an ending is the gate's own: the literal of its judging statement, or the value of the gate's
own variable at the moment it started the child. The rows registered for the build are `reasoncourt-preregistered`,
`reasoncourt-register`, `reasoncourt-source`, `reasoncourt-watch`, `reasoncourt-sealers` and `reasoncourt-fence`.

**Numbers that moved between the court and the registration, each by the owner's own test.**

- **23 / 15 / 45 of 83 codes, not 24 / 16 / 45 of 85.** `chain_hash` is named in `RUNGS.md` as the envelope's
  function and not as a refusal, so it is first registered here. `SHELL-ADMIT-PARSE` is `ADMIT-PARSE` as the shell
  prints it: one code. `LIVEINPUT-SCREEN-DIFFERS` belongs to a detection, which is outside.
- **63 program-owned courts, not 64.** One of the 64 was the gate's own `main`, a pointer and not a court.
- **Nine endings in prose, not six.** The first check counted an ending as held if any one of its codes was in a
  head. `readercourt-writers` requires two, and the reader's code stands in parentheses after `LIVESESSION-FORM`.
- **A 22nd sealer statement.** `admit-replay`'s sealer check holds the word "envelope", so it was not among the 21
  that hold nothing. Its sixteen forged envelopes are read by the same rule.

**Dev notes.**

- **A mechanical witness can pick the gate's own prose.** The first witness search took, for several codes, a
  sentence the row returns on success or raises on failure, because the code's name occurs there too. A literal
  inside a `raise` or a `return` is now never a witness, and every witness that is not in the judging statement
  itself was read by eye. Five were corrected by hand and are marked.
- **The gate's own variable, nearest first.** The expected code of an ending was read from the gate's variables at
  the moment it started the child. Reading the row's frame before the helper's took a stale loop variable for 64
  endings; the frame nearest the child is read first.
- **A commit's name is local.** The census was taken at `0f80bb7` here; the same patch is `b077eef` on the host,
  because `git am` writes a new commit. The registration pins the file's sha256 and the patch number, not a commit.
- **A listener can redden a row.** Wrapping the sealers' functions to listen made `hoststate-fence` red, because
  that row reads a sealer's source through the function object. The gate itself was untouched; the build's
  listener has to leave the function's source readable.
- **Five statements are marked as owed a code** (`text-refuse` twice, `workshop1-propose`, `liveinput-court`,
  `bearing-refuse`'s eye on rock): the row judges the refusal for its reason and holds a word or an exit status
  only. The mark is the registration's own addition and is the owner's to strike.

**On the host (DANIELDILLBERG, 2026-10-05): pushed.** 0117 and 0118 were applied and the gate read `GATE PASSED`,
rowset `39e5874a7127cfa4`, 226 rows / 0 fail / 0 skipped. The owner pushed `b077eef..c057da2`. From that push the
entry and the register are fixed: a correction is an amendment entry with its own hash.

**A review of the register's counts, and the ruling.** A review the owner brought read the register's `counts`
block against the entry and found a name that does not say what it counts: `endings_with_one_code_in_prose: 3`,
beside an entry, a record and a list of corrections that all speak of nine endings in prose. The numbers are right
and the name is loose. Read as a flat partition the counts give 1,072 + 23 + 2 + 6 + 3 = 1,106, which is not 1,103.

| | |
|---|---|
| the partition, in the entry's own sentence | 1,072 in a code head + 23 `REFUSE(any)` + 6 held only by their row + 2 unjudged = 1,103 |
| the three | `readercourt-writers`' endings (A177): `LIVESESSION-FORM` is in the head and the reader's code is in prose, so they are inside the 1,072 |
| the nine in prose | the 6 held only by their row, and those 3 |

The owner's ruling: **hold it in the build**, with no amendment. *The authority for the reading already exists in a
registered artifact; the row would not be inventing an interpretation, it would be holding the entry's own words
against the register's counts.* The build's `reasoncourt-register` row asserts the four-part sum, the three as a
subset of the 1,072, and 6 + 3 = 9; it is planted with the flat misreading and must refuse it; and it cites the
entry's sentence as its witness for the partition, *so the reading stands on registered text rather than on the
row's phrasing of it.* An amendment that changes no number would restate what the entry says, and MOUSE-LOOK-0a's
precedent is for a changed scope, not a clarified name.

**Configurations, not runs.** The gate takes no input. For one tree, the children it starts and how they end are a
function of the platform and of which records are present, and of nothing else; two passes read byte for byte the
same for that reason. So what stands between the register and "it holds" is a short list of configurations and not
an open set of runs: this container, this container with the host's records, and the host. A listen-only pass was
made in the first two and then, by the owner, on the host, each off the gate, with one instrument kept outside the
repository (sha256 `fb593b18…d729`). It runs the gate once, keeps every child that does not end 0 with the code
heads of its lines, and lays them beside the pushed register by the registered rule.

| configuration | interpreter | records present | gate | endings heard / registered | groups that hold | findings |
|---|---|---:|---|---:|---:|---|
| the container | Python 3.11 | 0 | 226 / 0 fail | 1,103 / 1,103 | 77 of 77 | none |
| the container | Python 3.12 | 0 | 226 / 0 fail | 1,103 / 1,103 | 77 of 77 | none |
| the container, with the host's records | Python 3.12 | 31 + 2 | 226 / 0 fail | 1,103 / 1,103 | 77 of 77 | none |
| the host, DANIELDILLBERG (win32) | Python 3.14 | 31 + 9 | 226 / 0 fail | 1,103 / 1,103 | 77 of 77 | none |

No ending fell outside the watch's scope and none was in no group. The owner's ruling: **the host is heard before
the build**, with the same instrument byte for byte, so that the two sides differ only in platform. His reason:
the six rows will rest on the 1,103 and the 77, so the first Windows run of the build is no longer a probe; a
platform difference found before the build is the same amendment *settled in calm*. What a pass hears is OBSERVED,
one run, and never the source of an expected value. A difference is a finding settled by amendment, never a
tolerance.

**Heard on the host (DANIELDILLBERG, 2026-10-05).** Patch 0119 was applied there and pushed (`c057da2..f145a8d`,
as the host's own refs read). The owner then ran the instrument, the same bytes (`fb593b18…d729`), on win32 under
Python 3.14.5 with 31 + 9 records present.

| what the host's pass heard | |
|---|---|
| the gate inside the pass | exit 0, 226 rows, 0 failed, 0 skipped |
| endings | 1,103 heard, 1,103 registered |
| groups | 77 heard, 77 registered, 77 holding |
| exit statuses | 2 in 1,090 endings, 70 in 11, 1 in 2 — the same three numbers as in each pass here |
| outside the watch's scope | 0 |
| findings | none |

Group by group, the host's list is the container's. Its report (sha256 `65a23272…5bbf`) is kept beside the
instrument, outside the repository. So the fourth configuration reads as the three here did, and the build's six
rows will rest on counts heard on both platforms and under three interpreters. That is OBSERVED, one run in each
configuration. It was never the source of an expected value, and it changed nothing in the register.

**Where the in-process gap is, and what was counted there (an experiment beside the register).** The watch's
substrate is the process boundary: a return code and bytes on a pipe. A refusal that is raised, caught and compared
inside the gate's own Python never crosses it. The owner's reading: the information is whole at the moment the
exception is minted and is destroyed at the judging site, so the tap belongs upstream, where it is born. The same
instrument therefore listens to the interpreter's own raise events (`sys.monitoring` from Python 3.12,
`sys.settrace` before), counting each exception once, in the frame that raised it. It wraps nothing: no function,
class or module of the tree is touched, and `hoststate-fence`, which a wrapping listener had reddened, stays green.

| refusal types minted in the gate's process, one run | mints | where |
|---|---:|---|
| the sealers' `Refuse` (five classes) | 74 | the ten sealer rows and `admit-replay` |
| `envelope.EnvelopeViolation` | 32 | `records-firewall` 2, `readercourt-writers` 4, `readercourt-commands` 26 |
| `savedform.Refused` | 141,977 | `readercourt-agree` 141,870, `-commands` 68, `-language` 36, `-writers` 3 |
| all refusal types | 142,083 | 16 rows, 59 raise sites |

The three configurations here gave the same counts, type by type and site by site, under both taps, and the
host's pass gave them again under Python 3.14 (146,318 exceptions of every kind were raised in its gate process,
142,083 of them of a refusal type, at 59 sites). What the census shows beside the register:

- **Every mint but one is claimed.** The 74 are the 57 planted records and the 16 forged envelopes, and one more.
  The 32 are the eight coded statements that judge the envelope. The reader's 141,870 in `readercourt-agree` are
  the 163,072 mutants less the 21,202 accepted, which is the agreement court, outside this rung.
- **The one more** is raised by the gate itself (`verify.py` line 1317): a planted failure that makes a sealer's
  restore path run, and is tolerated, not required. It is the in-process twin of `shell-build`'s dropped ending.
- **A mint is not every in-process refusal.** Thirteen statements judge a refusal that is neither a child's
  non-zero ending nor an exception in the gate's process: a trace line, a returned list, an `unavailable` snapshot,
  a digest of verdicts, a verdict line written by a worker. No tap on
  raises hears them. They are already data.
- **Worker processes are not heard.** The corpus court runs the Python reader in workers.

**The owner's ruling on the gap: live with it, measure it, and seat nothing now.** The registration stays as narrow
as it says it is. Two things are recorded as declared, each for a court of its own:

1. **An accounting, not an extraction.** A text the owner brought proposed to derive the register from the gate's
   syntax tree. The census's own syntax pass had found 76 of 190 statements, so the tree cannot classify: *what
   distinguishes a refusal check from a detection or a gate-self check is the row's intention, not its shape.* What
   survives is narrower and decidable: every comparison of an exit status and every handler of a refusal exception
   must be a registered statement or a named non-refusal. *That is not classification; it is conservation.* Folding
   it into this rung was rejected: the edge exists so that the rung is not a general strengthening of assertions,
   *and an accounting is the most tempting possible widening because it looks like bookkeeping rather than scope.*
   Its known hole, to be registered with it: a refusal judged by another shape, such as a word looked for in the
   output with no exit status and no exception, is invisible to it.
2. **A refusal as an emission and not an interruption, for the gate's own process.** The owner separated two
   questions. Whether the machine can learn the classification: no, as above. Whether a refusal can be a datum
   that flows through a channel and is claimed, as the children's are: yes, and the tree has done it three times
   already — the readers return a verdict line, the children write records to a refusal log that a row holds in
   bijection with what they print, and a planted death is a typed ending. It cannot happen in this rung: turning a
   sealer's `raise` into a returned verdict changes every sealer's interface, which the fence forbids. It is a
   later rung, with its census first, and the count above is that census.

**What stands against the tree, on reading those two (a review, not a ruling).**

- **Visibility and vocabulary are two gaps.** A tap on raise events gives the first with no change to any sealer:
  every mint can be counted and claimed. It does not give the second. The sealers have no codes, and the one thing
  a mint carries besides its type is its raise site, which is a branch inside a program; by the first court's
  ruling a branch is never authority. A reason for an in-process refusal needs a code, and a code is a change to
  the sealer.
- **The sealers already emit at their own process boundary.** Run as a command, a sealer prints `REFUSE: …` and
  ends 2, and `readercourt-commands` judges one that way. The gate calls them as functions because their commands
  do the host's work.
- **The text's other layers.** The witness literals it proposes to extract are already in the register, 215 of
  them, and the registered `reasoncourt-source` row is what holds them. Its third layer would run the gate over
  "its own mutation corpus"; the 163,072 mutants are inputs to the readers inside two rows, and the gate itself
  has no input to vary. Its figure of 19 in-process refusals is not a number of this tree. Its formal-semantics
  step is declared and not on the route.

**What became of the gap (the fifth court, 2026-10-05).** The owner took the visibility half as a slice of its
own, MINT-WATCH-0, registered in the next section and built after this rung. The vocabulary half stays deferred: no
exception is required to carry a code. Nothing of this rung's entry, register or rule moved.

**Built (2026-10-05), against `337ab021`, which is not edited.** One file changes: `verify/verify.py`. No program, no
sealer, no record and neither register changes. `verify/mints.json` is not read by this build (the owner's ruling:
the process-boundary result is established on its own, before the mint watch exists).

```
  subprocess.run ──► the watch ──► ENDINGS        row · program · command · exit · the code heads of its lines
                                                  the text after a head is never kept; the child's result is untouched
  a registered row runs ──► the listener ──► SEALER_CALLS   row · function · the judged arguments · accepted | refused
                            the interpreter's own call and return events; no function wrapped or replaced

  reasoncourt-preregistered · -register · -source · -watch · -sealers · -fence            rows 227 to 232
```

| row | what it holds | plants, on every gate |
|---|---|---|
| `reasoncourt-preregistered` | the entry by its hash and its phrases; the register's 199,090 bytes by their hash; the gate's counts and its six rows are the entry's | — |
| `reasoncourt-register` | the register, read through the saved form's reader, is whole: its 27 counts recounted from its own content; every statement expects exactly one of a code, `REFUSE(any)` with its reason, or a death; every code has its source; every second witness names a refusal check; every slot names statements of its row, and the slots sum | the flat misreading of the counts; a part left out; a part miscounted |
| `reasoncourt-source` | the 165 judging statements, each in the function the register names; the 215 witness literals, each where the register says and holding its code; the sentences cited for 23 codes in the ledger, hash-locked; the lines cited for 15 codes in this file, word for word | a statement with its code taken out; a table with one code changed; a reworded line of this file; a reworded sentence of the ledger; a code that stands only in the gate's own failure text |
| `reasoncourt-watch` | every child that did not end 0, seated in a slot of its group: 1,103 in 77 groups, each group its number, each coded slot filled by endings that end as registered and carry the code in a code head, the rest exactly the open slots | eleven synthetic endings (the nine registered and two more); the run with one ending taken away, and with one moved to another row |
| `reasoncourt-sealers` | every call the 11 registered rows make of the 15 sealer functions: 57 planted records and 16 forged envelopes refused; 55 of them one registered mutation and its closure from a twin accepted in the same row; 18 still owed | a twin changed in a second field (a record, and a session given as bytes); a planted record accepted; a refusal not registered; one refusal too many; a debt that goes away; a listener that failed; a row not heard |
| `reasoncourt-fence` | by source: the watch, the listener, who reads the register, 39 Rust sources and 17 sealer files by hash, the 226 rows and the six, the two children started outside `subprocess.run` | — |

**What the gate heard here.**

| | |
|---|---|
| the gate | 232 rows / 0 fail / 0 skipped, rowset `5b48184218214583` |
| children that did not end 0 | 1,103: 1,090 ended 2, 11 ended 70, 2 ended 1 |
| groups | 77, each with its registered number; none empty, no ending outside one |
| code heads kept | 1,104 in all; no ending kept more than two |
| calls of sealer functions in the registered rows | 158 heard; 150 by a registered row and function: 73 refused, 77 accepted |
| the listener | `sys.settrace` on Python 3.11; `sys.monitoring` on 3.12, 3.13 and 3.14.0rc2; the same 158 calls on each |

**The listener.** The entry registers that the gate *listens to every call the registered rows make of the registered
sealer functions, without changing a function or its result*. A wrapper around a sealer function had already
reddened `hoststate-fence`, which reads a sealer's source. So the listener takes the interpreter's own events: where
`sys.monitoring` exists, the start and the return of the fifteen functions' code objects and the unwinding of a
frame; before it, a trace function that follows only those functions' frames. It is on only while one of the eleven
registered rows runs. It copies the judged arguments as the call starts, notes whether the call returned or was
refused, and touches nothing.

**Readings the build made.** Each is the owner's to strike before the push.

1. **Seating, not first fit.** The entry says each coded slot *is filled by* endings that carry its code, and what
   is left *numbers exactly* the open slots. The row finds an assignment of every ending to a slot it fits, each
   slot holding exactly its count. The listening instrument had taken the first endings that fit.
2. **Every line's code head is kept.** The instrument kept the first 200 lines of a stream and 40 heads. More heads
   can make a code present and never absent.
3. **What "no file" is.** *No file under kernel/, shell/ or workshop/ differs* is held as every Rust source there
   (39), by hash, and the set of them. The folders' READMEs are documents and their `attest/` folders hold records;
   neither is pinned. *No sealer under verify/* is held as 17 files: the eleven sealer modules, `diagcommon.py`
   and the five `seal_*.py`.
4. **A planted session is compared, not read.** A forged session reaches a sealer as bytes. The row compares it
   with its twin member by member through `json.loads`. The saved form's reader is not called on forged bytes, so
   the row raises no refusal of its own.
5. **One inner call is named.** `seal_livesession` calls `check_saved`, so `livesession-sealer`'s five planted
   records are refused twice over. The row judges the outer call, and the inner pair is named in the gate. Any
   other refusal with no registered record is a finding.
6. **Two more kinds of finding.** A failing child that is no program of the tree, the gate's Python or the
   compiler, and an ending the watch failed to keep. The registration counted none of either.
7. **Without `rustc`** the watch's row and the sealers' row skip, as the rows they depend on do.
8. **The counts are read as ruled.** `reasoncourt-register` takes the five numbers out of the entry's own sentence,
   holds the register's counts to them, and cites the sentence and the phrase *whose LIVESESSION-FORM is in the
   head* in its text. The flat reading, five parts, is planted and refused for counting three endings twice.

**Mutation testing, off the gate.** 37 planted defects, one at a time, each in a scratch copy of the tree. The rows a
defect touches were run live; the court's rows then judged, with one whole pass of the unchanged gate standing for
the rows not rerun.

| family | defects | caught | of those, with every earlier row still green |
|---|---:|---:|---:|
| a program or a row changes what ends (a code out of the head, a plant dropped, another exit status, another code, a longer code) | 5 | 5 | 3 |
| a sealer or its row (a plant with a second field, a sealer that stops refusing, a twin moved, the listener off) | 4 | 4 | 2 |
| the register, a judging statement, a cited text | 4 | 4 | — |
| the watch, the listener, the rows, the sources (by the fence, and the watch kept empty) | 9 | 9 | — |
| the court's own judging, weakened one rule at a time | 15 | 14 | — |
| all | 37 | 36 | |

- **The defects no earlier row saw.** A program that prints its code after a lower-case word, or lets the code
  grow a suffix, leaves five rows green, because they look for the code anywhere in the output; the watch refuses
  both. A row that stops giving one
  of its six bad edits to the program stays green; the watch counts five endings for six, and the source row finds
  the statement gone. A planted record changed in a second field is still refused by its sealer; the sealers' row
  says where it now differs.
- **One survivor, equivalent.** With the comparison of a group's number of endings removed, the seating still
  refuses a missing or an extra ending, because every slot must hold exactly its count. The line that survived only
  words the finding.
- **Two survivors of the first run became plants.** A literal inside the gate's own failure text taken as a
  witness, and a refusal beyond the registered ones ignored. Each survived, a plant was added to the row, and each
  is caught now.

**A registered limit, counted.** The entry says a coded ending that changed its code can be counted as its group's
open slot *if another ending carries the code*. Today that is so in three groups: `shell-blit-law`,
`refusallog-bijection` and `bearing-refuse` each have one more ending carrying the code than coded slots. In each,
one ending could lose its code and the watch would still seat it. The row's own statement judges those endings.

**The listening instrument over the built gate (off the gate, one run, Python 3.12).** The same instrument bytes
(`fb593b18…d729`). The gate inside the pass ended 0 with 232 rows. 1,103 endings heard and registered, 77 of 77
groups holding, no finding: the instrument and the gate's own row agree. 142,083 refusal-type exceptions at 59
sites, row by row what `verify/mints.json` holds, and none in the six new rows. So the condition MINT-WATCH-0
registered for these rows is met as observed: they mint no refusal, and its register needs no amendment for them.
The gate's listener and the instrument's ran together, each on its own tool id (report sha256 `4c288a8f…`, kept
outside the repository).

**Before the host ran it.** The whole gate ran here on 3.11 and, inside the instrument's pass, on 3.12. On 3.13 and
on 3.14.0rc2 the eleven listened rows and the court's rows that need no child were run, not the whole gate.

**On the host (DANIELDILLBERG, 2026-10-06): landed.** 0122 and 0123 were applied and the gate read `GATE PASSED`,
rowset `5b48184218214583`, 232 rows / 0 fail / 0 skipped, the six rows of this rung among them. The owner pushed
`a02d82c..a1c0a65`.

| | |
|---|---|
| the watch | `reasoncourt-watch` passed: the host's own gate seated its endings in the 77 registered groups. The count it printed is in the row's text, which a gate prints only under `--verbose`; this run was the compact one |
| the listener | `reasoncourt-sealers` passed: on the host's interpreter the listener heard the registered calls. Which tap it used is in the same unprinted text; the host's listen-only pass recorded Python 3.14.5, where it is `sys.monitoring` |
| the fence | `reasoncourt-fence` passed: the 39 Rust sources and 17 sealer files have on the host the bytes they have here |

So the register that was heard on the host by an instrument before the build is now held there by the gate itself.
None of the build's readings was struck before the push.

**Outside sources read for this (attributed; hypotheses about practice, not claims of this tree).**

- Rice's theorem, as a recent paper restates it: every non-trivial property of what a program computes is
  undecidable, and a decidable approximation must carry false positives
  ([Baldan, Ranzato, Zhang, arXiv 2105.14579](https://arxiv.org/abs/2105.14579v1)). Read here as: a syntactic
  pass can over-count candidates and be corrected by a list, and cannot decide which ones require a refusal.
- Static and runtime verification are described as complements: a monitor sees the executions that happen and
  cannot prove all of them, a static method can cover all and handles large interacting systems poorly
  ([Chimento et al., Chalmers](https://research.chalmers.se/en/publication/248733)). The gate's case is the easy
  end of that: it has no input, so its executions are enumerated by configuration.
- Bazel's definition of a hermetic test: its result depends only on its declared inputs, which is what makes the
  same test give the same result on every run
  ([Bazel test encyclopedia](https://docs.bazel.build/versions/main/test-encyclopedia.html)).
- A characterization test pins what software does, not that it is right
  ([Wikipedia, after Feathers](https://en.wikipedia.org/wiki/Characterization_test)). The register differs in one
  respect that matters: its expected side came from the gate's statements and registered text, not from recorded
  output.
- An executable semantics of Python exists for version 3.3 in the K framework and is incomplete by its own account
  ([Guth, University of Illinois](https://ideals.illinois.edu/items/45257)); the gate is twelve thousand lines of
  a later Python that starts processes.
- On Windows a child's exit status is an unsigned 32-bit number and there are no negative signal codes
  ([Python discussion](https://discuss.python.org/t/subprocess-returning-incorrect-exit-code-for-negative-exit-codes-in-windows-in-3-7/25917));
  Rust's documentation says exit codes have no portable meaning beyond success and failure
  ([std::process::ExitCode](https://doc.rust-lang.org/std/process/struct.ExitCode.html)). The register holds 2, 70
  and non-zero, which the programs set themselves; a crash would end differently on the two platforms, and none is
  registered.
- Rust checks a `match` over an enum for exhaustiveness at compile time
  ([rustc dev guide](https://rust.googlesource.com/rust-lang/rustc-dev-guide/+show/refs/heads/main/src/pat-exhaustive-checking.md)):
  the model of a completeness that is decided and not observed, available only where the reasons are one closed
  type.

**Grade.** DECLARED: the registration and the rulings of four courts; the accounting and the refusal as an
emission, each declared and not seated. OBSERVED (here, off the gate): the census, the derivation of the register
from the gate's own statements and variables, three listen-only passes in which every registered group held, and
the count of mints. OBSERVED (host, off the gate, one run): the fourth pass, in which the same 1,103 endings were
heard and the same 77 groups held; and one pass of the instrument over the built gate. ESTABLISHED (gate, here):
the six rows, 232 in the gate, on Python 3.11; the same six on 3.12 inside the instrument's pass. MEASURED (host):
the built gate, 232 of 232, one run.

**does_not_show.** That the census is complete: a check
it missed inside a row is not held, and nothing that happens inside the gate's own process is seen by a watch
(MINT-WATCH-0, built since, hears the raises there). That the host's pass makes the register true:
it was heard there once, by an instrument outside the gate. That a registered reason is the right reason: the court
will show that a refusal carries its registered code, not that the program's reasoning is correct. Anything about a
cause, where one code answers several.

**Falsifier.** A red row among the six on a later run of either machine with the tree unchanged. A registered requirement that does not stand in
`verify/verify.py` as patch 0116 left it. An expected value in the register that came from a program's output. A
planted record registered as meeting the condition that differs from its twin somewhere else. An ending of the
registered gate that is in no group.

## MINT-WATCH-0 — every refusal raised inside the gate's own process, claimed by row, class, site and count (preregistered `cd1472ec` and pushed; built: four rows, 236 in the gate; the gate passes here and on the host)

```
  the files' syntax ───────► the inventory (static)        8 refusal classes · 164 raise sites · 15 files
  no program is run          a site = file · function · the text of its raise statement   (line: a locator)
                                   │
  four listen-only passes ─► the measured layer            70 entries: row · site · count      142,082 mints
  one per configuration      a baseline for drift, never the source of a reason     + 1 plant of the gate
                                   │
  the interpreter's raise ─► the watch ─► every refusal mint of a pass has an entry, every entry its count
  event; nothing wrapped                  new row · new class · new site · a drifted count · unclaimed → red
```

**Where it came from.** REASON-COURT-0's watch stands at the process boundary. A refusal raised, caught and
compared inside the gate's own Python never reaches it. The listening instrument counted those where they are
made: 142,083 in a pass, the same in four configurations. The owner read the count and ruled.

**The owner's ruling (2026-10-05).** *This is a real slice, and I would take it — but keep its claim narrower than
"reason court."* It is registered as a separate slice, before any rung that would give a refusal a code or turn it
into a datum, and is not put into REASON-COURT-0 retroactively.

| | |
|---|---|
| LOCK | the listener on the interpreter's raise event, as an observational slice |
| REGISTER | MINT-WATCH-0: every refusal-type raise attributable to a row, a class, a site and a count |
| DEFER | requiring an exception to carry a semantic reason code |
| REJECT | treating the class or the site that was observed as newly minted authority for a reason |

**Three layers, kept apart.**

| layer | says | whose |
|---|---|---|
| the ending watch | what ended | REASON-COURT-0, at the process boundary |
| the mint watch | what raised | this rung, inside the gate's process |
| the reason table | what reason | REASON-COURT-0's register |

This rung adds visibility and completeness inside the process, and no vocabulary. It never says that a raise of a
class at a site means a reason.

**The fifth court: three answers.**

1. **Sites from source, counts measured.** The register has two layers and each is named for what it is. The
   owner locked that wording *rather than weaken REASON-COURT-0's rule*: an expected reason still never comes from
   what a program does, and this register does not learn what is correct from execution.
2. **A site is its text, with the line under a file pin.** The identity is the file, the function and the raise
   statement's own text. The line is recorded as a locator and is not the identity.
3. **Register now, build after.** This registration is a commit of its own; then REASON-COURT-0's build as
   planned; then this rung's. The two builds are not combined, and this one does not go first.

**The tap.** `sys.monitoring`'s RAISE event from Python 3.12, `sys.settrace`'s exception event before. A mint is
that event in the frame that raises, the one where the exception's traceback has no deeper frame; an exception
passing up through its callers is one mint. No function, class or module of the tree is wrapped or patched.

**The register, `verify/mints.json`** (46,076 bytes, sha256 `af5de1b4…acb6`, a document of the saved form).

*The static layer* is read from the files' syntax and from nothing else. A refusal class is an exception class a
Python file under `verify/` defines, other than the gate's two verdicts, `Red` and `Skip`.

| refusal class | raise sites | reached |
|---|---:|---:|
| `diagcommon.Refuse` (raised by seven sealers and by `diagcommon.py`) | 83 | 39 |
| `latency1.Refuse` | 19 | 4 |
| `presentscale.Refuse` | 16 | 3 |
| `envelope.EnvelopeViolation` | 14 | 5 |
| `framesplit.Refuse` | 14 | 2 |
| `latency1r.Refuse` | 13 | 2 |
| `savedform.Refused` | 4 | 4 |
| `diagcommon.CourtRefused` | 1 | 0 |
| all | 164 | 59 |

| file | sites | reached | never |
|---|---:|---:|---:|
| `verify/livesession.py` | 18 | 13 | 5 |
| `verify/latency1.py` | 18 | 3 | 15 |
| `verify/presentscale.py` | 16 | 3 | 13 |
| `verify/envelope.py` | 14 | 5 | 9 |
| `verify/framesplit.py` | 14 | 2 | 12 |
| `verify/latency1r.py` | 13 | 2 | 11 |
| `verify/presentexact.py` | 13 | 4 | 9 |
| `verify/allocreuse1.py` | 11 | 4 | 7 |
| `verify/presentstretch.py` | 11 | 3 | 8 |
| `verify/liveloop.py` | 9 | 6 | 3 |
| `verify/allocreuse.py` | 8 | 2 | 6 |
| `verify/drift.py` | 8 | 7 | 1 |
| `verify/diagcommon.py` | 6 | 0 | 6 |
| `verify/savedform.py` | 4 | 4 | 0 |
| `verify/verify.py` | 1 | 1 | 0 |

Fourteen of the files are pinned by their sha256: a change to one is a red pin and a decision. `verify/verify.py`
changes with every rung, so its one site is found by its text. One function holds the same raise text twice
(`savedform._read`); their order tells the two apart.

*The measured layer* is which row reaches which site and how often.

| row | entries | mints |
|---|---:|---:|
| `readercourt-agree` | 4 | 141,870 |
| `readercourt-commands` | 5 | 94 |
| `readercourt-language` | 4 | 36 |
| `admit-replay` | 8 | 16 |
| `liveloop-sealer` | 6 | 12 |
| `drift-sealer` | 10 | 11 |
| `presentexact-sealer` | 4 | 7 |
| `readercourt-writers` | 3 | 7 |
| `allocreuse1-sealer` | 4 | 6 |
| `latency1-sealers` | 5 | 5 |
| `livesession-sealer` | 5 | 5 |
| `framesplit-sealer` | 2 | 3 |
| `presentscale-sealer` | 3 | 3 |
| `presentstretch-sealer` | 3 | 3 |
| `allocreuse-sealer` | 2 | 2 |
| `records-firewall` | 2 | 2 |
| 16 rows | 70 | 142,082 |

| configuration | interpreter | tap | records present | refusal mints |
|---|---|---|---:|---:|
| the container | Python 3.11.15 | `sys.settrace` | 0 | 142,083 |
| the container | Python 3.12.3 | `sys.monitoring` | 0 | 142,083 |
| the container, with the host's records | Python 3.12.3 | `sys.monitoring` | 33 | 142,083 |
| the host, DANIELDILLBERG (win32) | Python 3.14.5 | `sys.monitoring` | 40 | 142,083 |

All four agree entry by entry and count by count. The layer is a registered measurement and is named as one: a
baseline for drift. It is not evidence that a refusal is right. A count is an expectation about an entry and not
the identity of an event.

**The plant.** One mint is the gate's own: `raise L1.Refuse("instrument failed")` in `overwrite_then_fail`, raised
in `latency1-sealers` to make a sealer's restore path run. Its row tolerates it and no statement requires it. It is
registered as a plant, the one exception to attribution, and is the one mint that makes 142,082 into 142,083.

**Never reached.** 105 of the 164 sites were reached in no configuration. They are registered as never reached, so
that a first mint at one is seen. Nothing is said about whether they should be reached. Many are a sealer's host
path or its command line, which the gate does not run.

**What the watch will refuse.**

| a pass in which | is |
|---|---|
| a row with no entry mints a refusal | a new row |
| a class of the tree that the register does not hold is minted | a new class |
| a site outside the inventory, or not registered for its row, mints | a new site |
| an entry is heard more or fewer times than its count | a drifted count |
| an entry of a row that ran is not heard, or a mint has no entry | unclaimed |

Each is planted on every gate as a made-up mint given to the same check. Through the tap itself the row also
plants three live cases: a refusal raised several frames down and caught at the top is one mint, at the frame that
raised it; an exception of a class that is not the tree's is not read as a refusal; a refusal raised and caught is
heard although nothing judged it.

**What the registration added to the rulings.** Each was written into the entry before the commit was pushed and
was the owner's to strike. They came from asking what the rows not yet built would do to this watch.

- **The rows measured are the 226 of rowset `39e5874a7127cfa4`.** REASON-COURT-0's six rows are not built and were
  not heard. They are held to the rule of any row. So before this watch is gated, those rows mint no refusal, or
  their entries are registered by an amendment with its own hash, heard the same way and named as measured. The
  watch never takes an entry from its own run.
- **This rung's own rows.** `mintwatch-watch` runs last of the four and judges what was minted before it began.
  The three before it have no entry, so they mint no refusal. What the watch's row mints in its live checks is
  judged there, against what it planted, and is not in the register.
- **A row the gate skipped.** Its entries are not expected in that pass, and the row's text names them. No pass
  named here skipped a row.

**Scope.** In: refusal-class raises in the gate's own process. Out, by name: the endings of child processes, which
are the other watch's; the thirteen statements of REASON-COURT-0's register that judge a refusal without a raise
(A058, A063, A067, A071, A072, A088, A112, A113, A115, A139, A144, A148, A171), which are already data; exceptions
raised in worker processes (the Python reader that `readercourt-corpus` runs through `verify/savedform.py
--splice`); and the vocabulary of diagnostics.

**Rows registered for the build:** `mintwatch-preregistered`, `mintwatch-inventory`, `mintwatch-fence`,
`mintwatch-watch`.

**On the host (DANIELDILLBERG, 2026-10-05): pushed.** 0120 and 0121 were applied and the gate read `GATE PASSED`,
rowset `39e5874a7127cfa4`, 226 rows / 0 fail / 0 skipped. The owner pushed `f145a8d..a02d82c`. From that push the
entry and the register are fixed: a correction is an amendment entry with its own hash.

**The owner's ruling with the push.** *I would not change the order or reopen the registration.*

| | |
|---|---|
| the order | REASON-COURT-0's registration, its build, this registration, this build. The registration is frozen before its implementation exists |
| what this rung is under | the registered vocabulary of REASON-COURT-0, and not its execution: REASON-COURT-0's build does not read `verify/mints.json` |
| what the register is | *a frozen measurement register, with static site identity plus four-configuration observed counts* |
| the 105 sites never reached | they *remain exactly that — reach-map facts, not planted refusal expectations* |
| the scope | the 226 rows, the skipped-row exclusion, the watch's own row and the `latency1-sealers` plant stay *explicit rather than being silently generalized* |
| up to its own row | correct as registered: *it prevents a watch from retrospectively claiming authority over later rungs* |
| this rung's build | the tap is listen-only and judges the raises of a pass against the frozen register; *the expected values are not regenerated from that run*. If the 71 measurements recur, that confirms the registered measurement. If one drifts, the row is red, *even if the same refusal type still occurs elsewhere in the row* |

**A provenance fact, and how it is held.** Patch 0121 wrote that 0119 was pushed as `c057da2..f145a8d`. That range
was read from the host's refs, read-only, and not from the owner's own output. His ruling: it is *a Git provenance
fact, not something REASON/MINT should infer from gate behavior*; the sentence stays if the range is the actual
one, and is corrected before the next push if it is not. What his own output shows is consistent with it and is not
a second witness of the range itself: the push of 0117 and 0118 ended at `c057da2`, and this push began at
`f145a8d`.

**Built (2026-10-06), against `cd1472ec`, which is not edited.** One file changes: `verify/verify.py`. No program, no
sealer, no record and neither register changes. Nothing of REASON-COURT-0 changes: its six rows are pinned here by
the hash of their text.

```
  the gate's file is read ─► the tap subscribes ─► MINTS    row · class · file · line · function ─► a count
                             to the interpreter's           text and a number; no exception, traceback or frame
                             own raise event
  mintwatch-preregistered · -inventory · -fence · -watch                              rows 233 to 236, the watch last
```

| row | what it holds | plants, on every gate |
|---|---|---|
| `mintwatch-preregistered` | the entry by its hash and its phrases; the register's 46,076 bytes by their hash; the gate's counts and four rows are the entry's | — |
| `mintwatch-inventory` | the static layer against the tree, with no program run: the 8 refusal classes are the exception classes the 32 Python files under `verify/` define, less `Red` and `Skip`; the 164 sites are the raise statements of those classes, each by file, function, text and order among equal texts; 14 files by hash; the gate's one site by its text; the 13 counts recounted | on a small tree given to the same reader: a line inserted above a raise makes no new site; a changed text, a second raise with the same words, a raise moved to another function, a raise taken out, a raise under another name and a new class are found. Against the real inventory: one raise more, one site gone, one class more, one class gone, a changed pinned file |
| `mintwatch-fence` | by source: the tap, what it keeps, who reads the register, that no function of this rung reaches the reason register and none of REASON-COURT-0's reaches a mint, the thirteen statements out of scope, REASON-COURT-0's rows text for text, the sources and sealers by hash, the 232 rows and the four | — |
| `mintwatch-watch` | every refusal raised in the gate's process before this row began: each of the 70 measured entries exactly its count, the gate's plant once, nothing else | nine made-up changes to the mints, a failed tap, an unheard row that was not skipped and a skipped row that minted; and three live ones through the tap |

**What the gate heard here.**

| | |
|---|---|
| the gate | 236 rows / 0 fail / 0 skipped, rowset `cb2f68e75e338768` |
| refusal mints before the watch's row | 142,083, in 16 rows at 59 sites: the 70 measured entries, each its count, and the gate's plant |
| by class | `savedform.Refused` 141,977 · `diagcommon.Refuse` 62 · `envelope.EnvelopeViolation` 32 · `latency1.Refuse` 4 · `framesplit.Refuse` 3 · `presentscale.Refuse` 3 · `latency1r.Refuse` 2 |
| in REASON-COURT-0's six rows and this rung's first three | none |
| in the watch's own row | 2, both its live plants |
| the tap | `sys.settrace` on Python 3.11; `sys.monitoring` on 3.12 and 3.14.0rc2; the same 71 keys and counts on each |

**The live plants.** After it has judged, the watch's row raises through the tap itself. `envelope.validate({})`,
called seven frames down and caught at the top, is one mint, at `validate` and at none of the frames it passed
through. A `ValueError` and the gate's own `Red`, raised and caught the same way, are not mints. A second refusal
of `envelope.validate`, caught with nothing looking at it, is heard. Both sites are ones no measured row reaches.
These mints are in the watch's own row, judged there, and are not in the register, as registered.

**Readings the build made.** Each is the owner's to strike before the push.

1. **One line of the row harness, and nothing of REASON-COURT-0.** An interpreter before 3.12 has one trace
   function per thread, and REASON-COURT-0's listener takes it while a sealer row runs. So on that interpreter the
   tap stays the thread's one trace function and hands a sealer function's frame to that listener as well: `row()`
   calls the tap once more after the listener starts. No function of REASON-COURT-0 is edited, and the fence pins
   its six rows text for text. Both heard what they had heard apart: 158 calls and 142,083 mints.
2. **When the tap subscribes.** As the gate's file is read, before any row, so that the first row is heard. Under
   `sys.monitoring` it takes the first free tool id of 4, 5, 2, 1, 0; REASON-COURT-0's listener holds 3.
3. **One switch on a traced frame.** Under `sys.settrace` the tap turns a frame's line events off. That is an
   attribute of the interpreter's frame, not of a module, a class or a function; the instrument that took the
   measurement set the same switch. The fence allows that one assignment and no other.
4. **What "returns nothing" is.** The `sys.monitoring` callback returns nothing. A trace function must return
   itself to stay subscribed, and returns nothing else.
5. **The line is used as the locator it is registered as.** A mint arrives with a file and a line. The row finds
   today's raise statement on that line, then knows the site by its file, function, class, text and order. The
   frame's own function name is not compared.
6. **A file name is read from where the gate was started.** The gate's own file can be named relatively, and a row
   may leave the working directory elsewhere; the tap keeps the starting directory, as text.
7. **A skipped row was never seen.** No pass skipped a row, so that rule is held by plants alone.
8. **Two pinned files are not sealers.** `envelope.py` and `savedform.py` are held by the inventory's fourteen
   hashes, and not by the fence's seventeen sealer files.

**Mutation testing, off the gate.** 39 planted defects, one at a time, each in a scratch copy of the tree, and two
runs with no defect, which must pass. The rows a defect touches were run live and one whole pass of the unchanged
gate stood for the rest.

| family | defects | caught | of those, with every earlier row still green |
|---|---:|---:|---:|
| a sealer or a row changes what is raised | 9 | 9 | 7 |
| the register, the tap, the fence's subjects | 12 | 12 | — |
| this rung's own judging, weakened one rule at a time | 18 | 18 | — |
| all | 39 | 39 | |

- **What only this watch sees.** A quiet row that raises a refusal and swallows it, and a second planted failure
  in the gate's own file: each leaves every earlier row green, REASON-COURT-0's six among them (run against them to
  see). REASON-COURT-0's listener hears fifteen sealer functions in eleven rows; 142,009 of the 142,083 mints are
  raised outside those functions.
- **What both see, differently.** A planted record that trips another check of its sealer: the row sees the same
  refusal. REASON-COURT-0 says the record now differs from its twin in two fields. This watch says two counts moved,
  one site a mint more and one a mint fewer, the class and the row the same.
- **Three survivors of the first run became plants.** A class, a raise and a missing site, each let pass when it
  was the only difference: the first plants had changed two things at once. Each is now given alone.
- **A defect in a pinned file that is not a sealer** is caught by the inventory and not by the fence, as reading 8
  says.

**Before the host ran it.** A whole pass here ran on Python 3.11 and on 3.14.0rc2.

**On the host (DANIELDILLBERG, 2026-10-06): landed.** 0124 and 0125 were applied and the gate read `GATE PASSED`,
rowset `cb2f68e75e338768`, 236 rows / 0 fail / 0 skipped, the four rows of this rung among them. The output the
owner gave ends at the gate: no push is in it, and none is written here.

| | |
|---|---|
| the watch | `mintwatch-watch` passed: the refusals raised in the host's own gate process were the register's, entry by entry. The fourth configuration, heard there by an instrument on 2026-10-05, is now held there by the gate |
| the inventory | `mintwatch-inventory` passed: the host's files under `verify/` hold the registered classes and sites, and the fourteen pinned files their hashes |
| the fence | `mintwatch-fence` passed: REASON-COURT-0's six rows are on the host the text they are here |
| what was not printed | the run was the compact one. The rows' texts, which carry the counts and name the tap, are printed only under `--verbose` |

None of the build's readings was struck. No finding, so no amendment.

**The seam is frozen (the owner's adjustment, 2026-10-06).** With this landing he ruled that the gate system stops
growing unless a real engineering invariant is found, and that the work is now the design environment. The ruling
and its decision rule are in [`docs/ROADMAP.md`](../docs/ROADMAP.md).

**Grade.** DECLARED: the registration, the fifth court's rulings and the ruling with the push. OBSERVED (off the
gate, one run in each of four configurations, by an instrument outside the repository): the measured layer.
ESTABLISHED (gate, here): the four rows, 236 in the gate, on Python 3.11; the same on 3.14.0rc2, one pass.
MEASURED (host): the built gate, 236 of 236, one run.

**does_not_show.** That any refusal is right, or that a class at
a site means a reason. That a fifth configuration would count the same. That a refusal which is raised is judged: a
mint is counted where it is raised, and what catches it is not seen. Which input drew a mint: counts are by row and
site. Anything about the 105 sites beyond that they were not reached. Anything about a row placed after the
watch's: it is not heard by it.

**Falsifier.** A red row among the four on a later run of either machine with the tree unchanged. A raise statement of a refusal class in the tree that the
inventory does not hold, or a site it holds that the tree does not. A gate pass, in a configuration named here,
whose mints differ from the measured layer. An entry of the register that was taken from the watch's own run.

## DESIGN-EVENT-0 — a canonical batch refused whole, or admitted by one admission as N ordinary edits equal to the same operations one at a time (preregistered `ae7cbb36` and pushed; built: six rows, 242 in the gate; the gate passes here and on the host; pushed)

```
  a design: text · a mouse · a recipe · a model             content time, not certified
        │  compiled to the net change set, in the one order
        ▼
  VRDNP2 batch            6 + N lines · 1 to 4,096 operations · one byte form
        │
        ├─ shell design --dry-run ──────► one line: language · parent · digest · head · N
        │                                 nothing written                 │
        │                                                                 ▼ the binding
        └─ shell design --previewed DIGEST,HEAD ──► recognized · anchored · granted
                                                    each operation: the session's own push
                                                    all N in memory, or refused whole
                                                               │
                                                               ▼
                             one journal, one sealed file: S's events, then N ordinary edits,
                             each with the batch's envelope and its place k of N
                                                               │
                             shell loader · workshop · sealer: a batch is whole, or the session is refused
```

**Why there is a rung.** The design tool was built over ADMIT-0 as it stands, and running it measured the cost: a
design of 60 operations took about 20 s to preview and about 20 s to admit on the build container. ADMIT-0 admits
one operation per proposal and one proposal per run, and each run verifies the whole session. By the owner's
adjustment a new gate needs a new engineering invariant. This is one: it changes the certified program and its
language.

**The host ran the tool first (DANIELDILLBERG, 2026-10-06).** 0126 and 0127 were applied, and the owner ran the tool
on the design this section keeps coming back to.

| | |
|---|---|
| `new` | a project under `design\work`, a session sealed by the host's own `verify\build\shell.exe`, head `73571153c2fc…391c` printed in full |
| `grant` | `allow=open,close,paint cells=1,1,20,12 classes=floor` |
| `propose` | the text `room 6,3 16,10` · `entrance 6,6` · `entrance 11,10` · `open 11,11` · `paint floor 60,70,90`: 60 operations, 56 cells opened, 3 closed, 1 class painted |
| `preview` | CURRENT `73571153c2fc`, PROPOSED `c18a71f6af8d`; floor 332 to 385 cells, all reachable from the camera (a view); the shell admitted all 60 in the scratch root |
| `admit` | ADMITTED, 60 operations, head `73571153c2fc -> c18a71f6af8d` |

The build container had reached the same two heads from the same text. The proposal ids differ between the
machines, since each carries a nonce, and the envelope is not in the head. The output gives no time, no gate run
after 0126 and no push: none is written here. By the owner's word the public repository stood at `a1c0a65` when this
rung was registered, so MINT-WATCH-0's build and what followed it were on the host and not yet pushed.

**The lock (the owner, 2026-10-06).** *LOCK DESIGN-EVENT-0 as the next rung, and batch these seven properties into
that court. Don't add a separate gate for each theorem.* The seven, and where the registration holds each:

| the property | held by |
|---|---|
| one proposal, one admission | `designevent-admit` |
| a batch means its operations in order | `designevent-admit` against ADMIT-0's own admissions one at a time; `designevent-replay` against two independent replays |
| what is admitted is the net change set | `designevent-language` holds the normal form. The netting is a compiler's, and content time |
| what was previewed is what is admitted | the binding, in `designevent-admit` |
| replay stays the authority | `designevent-replay`, with the memo held against the unmemoised computation |
| a preview is not a second world | the dry run writes nothing, in `designevent-admit` |
| every editor speaks the same event | DECLARED for editors that do not exist. Held: one batch language, one recognizer, and the design tool changing a session through nothing else |

Two more of his sentences are registered as rules. *The correctness theorem is equivalence; the speedup is the
consequence you measure.* And: *Make the event batch itself the architectural object*, so the build may not be the
design tool calling the shell less often.

**What reading the tree found before the court.**

| found | where | what it forced |
|---|---|---|
| a head is `sha256(head ‖ tag ‖ witness)`, once per event | `shell/playback.rs`, `fold` | one log item folded once cannot have the head of N edits |
| all three verifiers refuse a proposal id that occurs twice, and any language but VRDNP1 | the shell's loader, `workshop/sessionwalk.rs`, `verify/livesession.py` | a batch changes all three, whatever its shape |
| every edit re-hashes the level (18,708 bytes) and the tiles (983,048 bytes) | `content_hex`, called by both edit pushes | about 4 ms an edit event on load: 0.023 s with no events, 0.262 s with 60, linear. A cell edit cannot change the tiles |
| the lattice is 48 | `kernel/mantle.rs` | a level has at most 2,304 cells, 2,116 off the border: no batch above 2,121 operations can be admitted |
| ADMIT-0's row plants an envelope naming `VRDNP2` as a language that is not VRDNP1 | `admit_replay` | the new language's envelope has to be told apart from that plant, which must stay refused where it was |
| the two refusal rungs pin every Rust source and sealer | `RSN_SOURCES`; `verify/mints.json` | the build needs an amendment entry for each |

**The court (four questions, the owner's answers).**

| the question | his answer | what he added |
|---|---|---|
| what a design event is in the log | N edits, one admission: **locked** | *"one design event" should not mean "one hash fold."* The N edits are N log items. The batch is the transaction boundary, not a replacement for the session's edit algebra. Contiguous, ordered k = 1..N, all or nothing. Undo's unit is the batch |
| what batches the language accepts | canonical only: **locked** | canonicalising belongs to the design compiler, not to the authority. It must be idempotent, or it is not a normal form. An inverse pair is refused *only because VRDNP2 represents a net change set, not because inverse edits are intrinsically illegal* |
| what "verify the delta" means here | full verification with an exact memo: **locked**. The delta claim: **deferred** | *Every admitted batch is replayed against a verified parent; unchanged witnesses may reuse their exact prior digest, but no historical computation is trusted merely because it was previously verified.* Not to be called a checkpoint. There is no new trust root |
| what a preview is at the seam | a dry run in the shell: **locked** | the dry run returns the parent head, the proposal digest, the proposed head and the language version, *otherwise "preview then admit" is merely convention rather than a formally coupled operation* |

**The claim, as registered.** A canonical batch of one to 4,096 typed operations is either refused whole, leaving
nothing, or admitted by one admission as that many ordinary edit events of the session's log; and then the world,
the head, the replay, the saved events and the session one steps back to are those of the same operations admitted
one at a time through ADMIT-0, in the same order, from the same parent. His first wording said zero-to-N operations
and one ordinary session event. The court settled both: a batch of no operations is not in the language, and one
design event is one admission.

**The language.**

```
VRDNP2
renderer=<64 of 0-9a-f>
bearing=<64 of 0-9a-f>
parent=<64 of 0-9a-f>
proposal=<64 of 0-9a-f>
operations=<N>                 1..4096, no leading zero
open <x>,<z>                   N operation lines, each one of these three
close <x>,<z>
paint <class> <colour>
```

Each line ends in one LF, with nothing before the first and nothing after the last. A coord, a class and a colour
are VRDNP1's. A batch is 322 to 74,059 bytes. The cell operations come first in row-major order (z, then x,
strictly ascending), then the paints in the order `wall0 wall1 wall2 wall3 floor`, strictly. So a target occurs
once and each typed batch has one byte sequence. VRDNP1 and `shell admit` are as registered; the batch has its own
command.

**The checks, in order, the first that applies.** `ADMIT-IO` · `ADMIT-SIZE` · `ADMIT-PARSE` · `ADMIT-RANGE` ·
`ADMIT-ORDER` (not strictly after the operation before) · `ADMIT-PREVIEW` (with `--previewed`: not the previewed
bytes) · `ADMIT-PROGRAM` · the loader's own refusals · `ADMIT-SESSION` · `ADMIT-ANCHOR` · `ADMIT-DUPLICATE` (the id is
in S's history under either language) · then each operation in order, `ADMIT-CAPABILITY` and `ADMIT-AUTHORITY`, the
refusal naming the operation's line · and last `ADMIT-PREVIEW` again (not the previewed head). `ADMIT-ORDER` and
`ADMIT-PREVIEW` are first registered here. The others name the reasons ADMIT-0 gave them. A refused batch leaves
no run directory, no journal and no file, at whichever operation it was refused.

**The envelope.** ADMIT-0's eight members and two more, `place` and `count`. Parent and head stay the chain's own
heads around each event, as for any envelope. What the N events share is the batch's identity: language, proposal
id, digest, identities, grant and count. A batch in a session is whole and contiguous, place 1 to place count in
order, or the session is refused by the shell's loader, the workshop and the sealer alike. A proposal id names one
admission.

**What a death leaves.** A run of a batch of eight is ended at twelve points.

| ended at | what is left |
|---|---|
| the bytes read · the batch recognized · every check passed and all eight applied in memory | no run directory |
| the journal opened · a record torn at place 1 | loads to S's head |
| a record torn at place 4 or 8 · a record flushed at place 1 or 4 | part of a batch: refused by the loader |
| a record flushed at place 8 · the temporary file written · the saved file moved into place | loads to the child's head, all eight envelopes intact |

S's bytes are unchanged after each. Nothing loads to any other head.

**A head registered before the seam exists.** The design in the table above is 60 operations in row-major order and
then the class, which is VRDNP2's order. Sixty ADMIT-0 admissions took the session on the build container from
`73571153c2fca1ae9412f82dff335fa134d3bc06fb785b0878a032cfa442391c` to
`c18a71f6af8d269095c2789b9887f160344f15bed17a88782b47e24cd77c1036`.
The host printed the same parent in full and the same first twelve characters of the result. The one batch of those
60 operations has to reach that head.

**A prototype came first, and the registration says so.** Before the entry was committed the seam was prototyped
against its draft, on the build container, in a tree that is not this one. Nothing of it is in the repository.

| what the prototype showed | what was done with it |
|---|---|
| the 60 operations as one batch reached the registered head | nothing: the head was fixed beforehand, from the sixty admissions one at a time. No expected value was taken from the prototype |
| the draft's memo plant, a tile edit that keeps the tiles' earlier digest, leaves the content as it was. The seam's own nothing-to-change check refuses it, so no file is ever saved and the workshop never sees one | the plant was rewritten before the commit: a cell edit that reuses the tiles' digest from before a paint |
| a shell carrying that wrong memo saves a file and reads it back as verified, because the read-back uses the same memo | registered as what the court shows: the in-process comparison and the workshop are the checks of the memo, and the shell's own read-back is not |
| ADMIT-0's fence counts names in the shell's source (`go_admitted(`, `admit_next(`, `self.pending`, the admit arm of the command line) | the batch seam has names of its own and a fence of its own; ADMIT-0's fence passes unchanged and says nothing about the batch |
| the gate as it stands, run against the prototype: 229 of 236 rows passed. `liveinput-fence` and `liveauthor-fence` each hold, by its text, the statement that computes an edit's content from the bytes | registered: the memo re-pins those two rows on purpose, and what they held moves to a comparison of values in `designevent-replay` |
| `readercourt-writers` holds the one path a journal record is written by; a batch's records written together and flushed once went round it | the prototype was changed, not the row: a batch's records go through that path one by one, each flushed. What N flushes cost on the host is not measured |
| the other four red rows: `reasoncourt-fence`, `mintwatch-fence` and `mintwatch-inventory` on the files and raise sites this rung changes, and `reasoncourt-watch` on two endings left unheard behind the two fences | as registered: two amendment entries; the two endings are heard again once the fences are re-pinned |
| the twelve deaths, the largest batch and eleven forged envelopes behaved as drafted | recorded as a limit: the registration is not blind in those |

One run, OBSERVED, and a prototype is not the build: the 60 operations previewed in about 0.03 s and admitted in
about 0.08 s, where ADMIT-0 took about 20 s for each; 2,120 operations admitted in about 1.1 s; a session of 60
edits loaded in about 0.03 s, where it had taken 0.26 s.

**The six rows, and what each is registered to hold.**

| row | holds |
|---|---|
| `designevent-preregistered` | the entry's hash, and the constants of the build against it |
| `designevent-language` | a hostile corpus through `shell design`, each case its registered code and line; every single-byte mutant of three batches refused or recognized with no second spelling; a Python oracle agreeing on every input; the oracle's writer idempotent |
| `designevent-admit` | the child of one batch equal to the last child of the same operations one at a time (three batches of one, a batch of eight, the design's 60); capability and authority refused at every place of the eight; anchor, program, session, duplicate; the largest batch the lattice admits, 2,120 operations; a batch of 4,096 refused; the dry run and the binding |
| `designevent-crash` | the twelve deaths |
| `designevent-replay` | the workshop and the sealer on every child; the largest batch's head from the gate's own Python fold; forged files, each differing in one respect, refused by all three; the memo against the unmemoised computation; a wrong memo, which the shell that carries it reads back as verified, found by the comparison and refused by the workshop |
| `designevent-fence` | one reader of the language; no second fold; a batch's envelope set by the batch seam and the loader alone, and `shell design` taking no plant; VRDNP1, `shell admit` and every earlier row as they were; the kernel and both identities unchanged; every ending of this rung's rows carrying its registered code |

**What the registration adds to the rulings.** Each was the owner's to strike before the commit was pushed: the
language's lines and its byte bounds; a separate command, `shell design`, so that `shell admit` stays as registered;
the two new codes and the order of the checks; parent and head kept per event, with the batch's identity in the
members its events share; the twelve deaths; the registered head; the lattice's bound, with 2,120 as the largest
batch and 4,096 held only as a refusal; and what the rung owes the two refusal rungs.

**What it changes in earlier rows.** Two, and they are named. LIVE-INPUT-0's fence and LIVE-AUTHOR-0's fence each
hold the statement `self.content = content_hex(&self.level, &self.tiles)` by its text, as the reference replay's
own. The memo replaces it with the hash of two kept digests. Both rows are re-pinned in the build, as SIM-TICK-0,
MOUSE-LOOK-0 and HOLD-WALK-0 re-pinned them before. What they held there, that an edit's content is the content
the reference replay computes, is held from then on by `designevent-replay`: against the unmemoised computation
in process, and against the workshop, which keeps no memo. A pin on a text becomes a check on values. No other row
of an earlier rung changes its text.

**What it owes the two refusal rungs.** REASON-COURT-0 and MINT-WATCH-0 each hold that no Rust source and no sealer
differs from what it was. This build changes some. So it carries two amendment entries, `REASON-COURT-0a` and
`MINT-WATCH-0a`, each with its own hash, naming the moved pins and the raise sites added to
`verify/livesession.py`. No earlier row may end or mint otherwise than registered. If holding that needs more than
the two amendments say, the build stops and the owner rules. This rung's rows run after both watches and are heard
by neither: its last row judges their endings by code head, with the reader REASON-COURT-0 fixed, and no statement
of this rung requires a refusal without naming its code.

**Deferred, by name.** Verifying only a delta. A checkpoint that lets replay be skipped. Any trust in a seal. A
design representation above operations, a design diff, constraints or readings in the shell (DESIGN-IR/DIFF, the
rung after this one). A model, a live loop, a window.

**The registration pushed from the host (DANIELDILLBERG, 2026-10-06).** 0128 and 0129 were applied, the gate read
`GATE PASSED`, rowset `cb2f68e75e338768`, 236 rows / 0 fail / 0 skipped, and the owner pushed. Git's own output:
`a1c0a65..b975fc5  main -> main`. That range carries MINT-WATCH-0's build, its landing, the design tool, and this
rung's registration.

**The owner's lock with the push.** *LOCK / PUSH registration.* He named two things to hold in the build, neither
changing the registered claim, and ruled on a third.

| his point | what the build does with it |
|---|---|
| the 2,120 and the 2,121 are both true: 2,121 is the bound the geometry gives, 2,120 the largest batch the court's level admits. He asked that the tests show 2,120 admitted, 2,121 refused by the authority at the first operation that cannot be made, 4,096 recognized and refused by the authority, 4,097 refused for its range | all four are in the rows. The 2,121 was not in the registered court and is added at his word: the largest batch and one operation more, the camera's cell, which is open already. Refused `ADMIT-AUTHORITY` at that operation, line 1,088, nothing left |
| the memo is the dangerous part: *memoized replay, saved file, memoized readback, "verified"* is a circle, and the court needs the memo and the computation with no memo side by side | `designevent-replay` holds exactly that, and the plant shows the circle: a shell carrying a wrong memo reads its own file back as verified |
| the order of the build: the two amendments, the recognizer and writer, the admission with its dry run and binding, the memo and its comparison, the whole-batch rule in the loader and the workshop, the six rows, the gate, the gate twice more, the registered head | followed, with one thing said plainly: the amendments name the built files by hash, so their text was written last and their commit placed first |

**Built.** One new file in the shell and changes to four programs, the sealer, the gate and the design tool.

| file | what it holds now |
|---|---|
| `shell/designevent.rs` (new) | the one reader of a batch's bytes; the writer; the run with its checks in the registered order; the dry run; the binding; the court in process |
| `shell/playback.rs` | the place and count beside an admitted event; the memo: two kept digests, each recomputed by the edit that changes its bytes |
| `shell/livesession.rs` | the envelope's two more members in the saved item; the loader's rule that a batch is whole; the batch's run; the memo's comparison |
| `shell/main.rs` | `shell design` and `shell design-selftest` |
| `workshop/sessionwalk.rs` | the same whole-batch rule, over a replay that keeps no memo |
| `verify/livesession.py` | the same rule; the record cites this entry and counts batches and their events |
| `verify/verify.py` | the gate's own recognizer and writer of the language; six rows; two fences re-pinned; the two amendments' pins |
| `design/` | a proposal is one batch, a preview the dry run, an admit bound to it. Content time, not a row |

**The six rows, as built.** 236 rows become 242; rowset `aa94c886190510c7`.

| row | what it found |
|---|---|
| `designevent-preregistered` | the entry at its hash, the language's bounds, the registered head. The two amendment entries, unedited, each citing the entry it amends and this one, against the gate's pins. PLANT: a mint at an added site, in a row the watch hears, is refused by the watch's own check |
| `designevent-language` | each of the 348 proper prefixes of a batch of three is `ADMIT-PARSE` at the line the gate's own recognizer names; 42 named cases end in their registered code at their line; of 562,432 single-byte mutants of three batches every one is refused or emitted byte for byte, and the gate's own recognizer agrees on every one; the oracle's writer gives a batch's own bytes from its operations reversed, rotated and shuffled |
| `designevent-admit` | five batches (three of one operation, the eight, the 60) each give the child of the same operations admitted one at a time: head, content, events. The 60 reach `c18a71f6af8d…1036` from `73571153c2fc…391c`. Sixteen twins of the eight are refused at their places. 2,120 operations are admitted; 2,121 and 4,096 are refused. Each of the court's 30 refusals is given by the dry run of the same bytes with the same code, line and words. The binding holds |
| `designevent-crash` | twelve deaths of the eight, as the table above: nothing; the parent's head; part of a batch, refused; the child's head with eight envelopes |
| `designevent-replay` | the workshop and the sealer verify six children and count their batches; the largest batch's head is the one the gate's own fold reaches, edit by edit; 28 forged files, each wrong in one respect, are refused for the envelope by the shell's loader, the workshop and the sealer; over 2,208 edits the memo and the computation with no memo give the same content; the wrong memo is found |
| `designevent-fence` | by source: one reader, no second fold, the dry run inside the run, the batch reached by `shell design` alone, each digest assigned where its bytes are edited. By what was heard: of 528 children these rows started that did not end 0, every one carries a registered code in a code head |

**The two amendments, registered with the build.** `REASON-COURT-0a` (`591b8d0b`) names five pins moved and one
file added. `MINT-WATCH-0a` (`4ad67feb`) names one pinned file of the mint register and seven raise sites added to
it. Both were written after the build was finished, because they name its files by hash, and both say so. Their
commit is the one before the build's.

| | REASON-COURT-0a | MINT-WATCH-0a |
|---|---|---|
| what moved | `shell/livesession.rs`, `shell/main.rs`, `shell/playback.rs`, `workshop/sessionwalk.rs`, `verify/livesession.py`; `shell/designevent.rs` added | `verify/livesession.py` |
| what is added | nothing to the register | seven sites, in `batch_place` and `check_batches`, registered as sites no row before the watch reaches |
| what stands | `verify/reasons.json`, byte for byte; its 165 statements, 83 codes, 1,103 endings; the six rows' text | `verify/mints.json`, byte for byte; its 164 sites, 70 entries, 142,082 mints; the four rows' text |
| how the gate holds it | the fence's pins carry the new hashes | the reading of today's inventory sets the seven aside only for exactly the amended file |
| on this build | every row before the watch ends as registered | every row before the watch mints as registered; ADMIT-0's plant naming `VRDNP2` is refused at the site it was |

**The two fences re-pinned.** `liveinput-fence` and `liveauthor-fence` now hold the memo's statements in the two
edit pushes: apply, the digest of the bytes the edit changed, the hash of the two digests, fold. What they held
before, that the content is the reference replay's own, is the comparison in `designevent-replay` and the
workshop's replay. `designevent-fence` holds that each digest is assigned where its bytes are edited and nowhere
else.

**What the build found.**

| found | what was done |
|---|---|
| the wrong memo makes the shell read its own file back as verified only where the parent's own history has no cell edit after a paint. Elsewhere the read-back replays that history under the same plant, reaches different witnesses, and refuses | the court plants it on the design's child, which is cells and then a paint. The registered sentence holds there. On the eight's child, whose parent begins with a paint, the planted shell's own read-back refuses its file: recorded, not held by a row |
| the court as first written left out a registered case: a key's edit standing between two places of a batch. An unenveloped event inside a batch was being refused by its neighbours' places, never by its own rule. A mutant that removed that rule from the workshop passed every row | the case is built: a session of two batches of four with a key's edit between them, relabelled as one batch of eight and resealed, chain untouched. All three refuse it, and the mutant is caught |
| the registered court asks that every refusal of the admission court come from the dry run with the same code and line. The first rows checked five | every one of the 30 goes through both |
| the loader's check that a place is not above its count never decides: a batch that is whole and in order cannot hold such a place | kept, as the envelope's form. Its mutant is equivalent and is named below |
| seven raise sites were added to the sealer, not nine: a miscount in a draft of the amendment, caught by the script that reads the file |  the amendment says seven and names each |

**Mutation.** 49 changes to the built programs, each run against the five court rows.

| | |
|---|---|
| caught | 48 |
| equivalent | 1: the loader reads a place above its count. The whole-batch rule refuses the same files, by another sentence |
| caught only after a case was added | 1 of the 48: the workshop taking an unenveloped event inside a batch. The missing case was the registered one above |
| where they were planted | the recognizer (9), the admission (14), the session and its memo (5), the loader (10), the workshop (4), the sealer (6), the command line (1) |

**The design tool, on the build.** `propose` writes one batch; `preview` asks the shell for a dry run and shows what
it would give; `admit` hands the shell the previewed digest and head, and the shell refuses bytes that are not the
previewed ones. Two texts with one net difference compile to the same bytes. The admitted bytes are kept in the
project, named by the head they gave. Its twelve checks pass. A project made by the earlier tool opens as it is; a
proposal left pending by it is refused as stale and proposed again.

**Observed, the build container, one sitting, best of five.** The owner's design of 60 operations through the tool:

| | through ADMIT-0 (0127) | through the batch |
|---|---|---|
| propose | — | 0.06 s |
| preview | about 20 s | 0.10 s |
| admit | about 20 s | 0.13 s |
| a session of 60 edits, loaded and verified by the shell | 0.26 s | 0.04 s |
| the same session verified by the workshop, which keeps no memo | 0.33 s | 0.35 s |

No time is a registered quantity and none is held by a row.

**On the host (DANIELDILLBERG, 2026-10-06): landed and pushed.** 0130, 0131 and 0132 were applied and the gate read
`GATE PASSED`, rowset `aa94c886190510c7`, 242 rows / 0 fail / 0 skipped, the six rows of this rung among them. The
owner pushed. Git's own output: `b975fc5..7e1d997  main -> main`. That range carries the two amendments, the build
and its record. The output he gave holds one run of the gate.

| | |
|---|---|
| the amendments | the rows of REASON-COURT-0 and MINT-WATCH-0 passed under the amended pins: the host's files are the ones the two entries name by hash, and no row before the watches ended or minted otherwise than registered |
| the registered head | `designevent-admit` passed: the host's own shell admitted the 60 operations as one batch, in the row's root, and reached `c18a71f6af8d…1036`, the head registered before the seam existed |
| the deaths | `designevent-crash` passed: the twelve deaths, on win32 |
| the memo | `designevent-replay` passed: the memo beside the computation that keeps none, and the wrong memo found, on the host's build |
| the fence | `designevent-fence` passed: every child these rows started there that did not end 0 carried a registered code in a code head |
| what was not printed | the run was the compact one. The rows' texts, which carry the counts, are printed only under `--verbose` |

None of the build's readings was struck. No finding, so no amendment.

**The built gate's host runs (DANIELDILLBERG), run by run.** Each read `GATE PASSED`, rowset `aa94c886190510c7`,
242 rows / 0 fail / 0 skipped. Each range is Git's own output; where the output he gave holds no push, the line
says so and none is written.

| run | the tree it ran on | its output given | pushed |
|---|---|---|---|
| 1 | the two amendments, the build and its record (0130, 0131, 0132) | 2026-10-06 | `b975fc5..7e1d997` |
| 2 | that tree with 0133, documents only | 2026-10-06 | `7e1d997..eba1951` |
| 3 | that tree with 0134, documents only | 2026-10-07 | `eba1951..5f8ab66` |
| 4 | that tree with 0135, documents only. Git's id of it: `f9c5a8108ae33f17418b6a62a96bdec6c5429dcb` | 2026-10-07 | not in its output; its commit went out with run 6's push |
| 5 | the same tree: the next command after run 4 | 2026-10-07 | the same |
| 6 | that tree with 0136, documents only | 2026-10-07 | `5f8ab66..83b0261`, which carries 0135 and 0136 |
| 7 | that tree with 0137, 0138 and 0139: documents, and one entry in the ledger (DESIGN-IR/DIFF-0's registration) | 2026-10-07 | not in its output; its commits went out with run 8's push |
| 8 | that tree with 0140 and 0141: documents, and one more entry in the ledger (the amendment) | 2026-10-07 | `83b0261..5c8ad19`, which carries 0137 to 0141 |
| 9 | that tree with 0142, documents only | 2026-10-07 | not in its output; its commit went out with run 10's push |
| 10 | that tree with 0143 and 0144: documents, and one more entry in the ledger (HERMENEUTICS-0's registration) | 2026-10-07 | `5c8ad19..11afebf`, which carries 0142 to 0144 |

A later host run of this gate is a line of this table. The dates are the days the outputs were given; the outputs
carry none of their own. Every host run was the compact one, so the rows' texts, which carry the counts, were
printed by none.

**FULL×2, as the owner defined it (2026-10-07).** His word with the build's push was that the full ×2 gate judge
this rung. The record of the second run then said in prose what that run was and was not. He replaced the prose
with a predicate over two runs, each with its tree `T` and its output `O`:

> **FULL×2 iff `TreeID₁ == TreeID₂` AND `GateOut₁ == GateOut₂`.**

Equality of outputs *means byte-identical canonical gate output, and both runs are required to execute against the
same tree identity.* The identity is the tree's, *not merely the commit hash*: *a tree/object digest is the natural
equality witness.* And identity has three values, because *`!=` is dangerous when identity was simply not measured*:

```text
  T1 == T2        → same-tree
  T1 != T2        → different-tree
  T1 ?= T2        → identity not established
```

> **`==` earns the claim; `!=` defeats it; unknown withholds it.**

| the case | what it is |
|---|---|
| `Run₁(T) == Run₂(T)` | FULL×2 |
| `Run₁(T) != Run₂(T)` | FAIL, not certified |
| `Run₁(T₁) == Run₂(T₂)` with `T₁ != T₂` | two agreeing runs, but NOT FULL×2 |
| `Run₁(T₁) != Run₂(T₂)` | not FULL×2 |

*Anything else is not certified FULL×2, without necessarily being called a failure.* His own reading of the second
host run:

```text
  T1 != T2
  Run(T1) == Run(T2)

  therefore:
  two-run agreement = TRUE
  same-tree condition = FALSE
  FULL×2 = FALSE
```

**The runs under it.**

| the pair | T | O | FULL×2 |
|---|---|---|---|
| host, runs 1 and 2 | `!=`: 0133 was applied between them, by Git's own output | `==`, as printed: the two outputs he gave, compared here line by line, 242 rows and the reconcile line | FALSE: two agreeing runs |
| host, runs 2 and 3 | `!=`: 0134 was applied between them, by Git's own output | `==`, as printed | FALSE: two agreeing runs |
| host, runs 3 and 4 | `!=`: 0135 was applied between them, by Git's own output | `==`, as printed | FALSE: two agreeing runs |
| host, runs 5 and 6 | `!=`: 0136 was applied between them, by Git's own output | `==`, as printed | FALSE: two agreeing runs |
| host, runs 4 and 5 | `==`: Git gave the tree's id before run 4 and after run 5, `f9c5a8108ae3…9dcb` both times, and `git status --porcelain` printed nothing both times; run 5 was the next command after run 4 | `==`, as printed: the two outputs he gave, the same character for character | **TRUE** |
| here, passes 1 and 2 on the head that carries this record | `==`: two exports of one commit, and a digest over each export's tracked files, taken before and after its pass, the same all four times | `==`: the two logs, byte for byte | TRUE |
| here, pass 3 against pass 1 | `!=`: the same export with the host's 33 records added | `==`: the logs, byte for byte | FALSE: an agreeing run on another tree, which is what that pass is for |

What this leaves stated.

- **On the host this gate is FULL×2, by its fourth and fifth runs.** The first three were each on a tree of its
  own: agreeing runs, and none of them a failure. Then the owner ran it to the predicate: the tree's id, the gate,
  the gate again, the tree's id. One tree, one output.
- **What the host's `T` is.** Git's id of the tree of the commit checked out, with a status that lists nothing: the
  tracked files are that commit's, and no file stands beside them that Git does not ignore. Files Git ignores are
  outside it, the gate's build directory among them. It was taken before the first run and after the second, and
  not between them.
- **The gate does not print a tree's identity.** Its reconcile line names the rowset, a digest of the row names,
  and nothing of the tree. So `T` is taken outside the gate: on the host from Git's output around the runs, here
  from the commit the passes were exported from and a digest of the exports. Where neither is given, `T` is `?=`.
- **`O` on the host is equality of what was printed.** The outputs were pasted and compared here. No digest of the
  gate's output was taken on the host.

**The judgement his word named.** *Let the full ×2 gate judge DESIGN-EVENT-0 as a complete engineering rung.* Under
his own predicate the host's gate is FULL×2 on a tree that holds this build: 242 of 242, twice, one tree, one
output. What he makes of that is his to say. No push was in the output he gave for those two runs; the commit
they ran on went out with the sixth run's push.

**His word after it (2026-10-07).** *take next.* By his order of 2026-10-06 the rung after this one is
DESIGN-IR/DIFF. It is not registered, and nothing of it is written here.

Earlier landings are not regraded. Their passes here were exports of one commit with no digest of the exports
taken, and their host runs are recorded as what they were, one run or two.

**The owner's word with the push.** *My word: push the build. Then don't immediately add another theorem. Let the
full ×2 gate judge DESIGN-EVENT-0 as a complete engineering rung.* Here the gate ran three passes on the head, their
logs identical. The host's output held one run then; its runs since are in the table above. No rung is registered
after this one and none is proposed here.

He asked that the memo's account keep its whole chain, and drew it:

```
  wrong memo
     ↓
  shell read-back can be fooled
     ↓
  independent comparison catches it
     ↓
  workshop catches it
     ↓
  honest shell catches it
```

*That is materially stronger than simply saying "the memo plant fails." It establishes why the memo comparison
exists at all.* Each step is something `designevent-replay` does:

| the step | in the row |
|---|---|
| a wrong memo | the plant: a cell edit reuses the tiles' digest from before a paint |
| the shell's read-back can be fooled | the shell carrying the plant closes one cell on the design's child, saves the file and reads it back as verified. This is so only where the parent's own history has no cell edit after a paint. On the eight's child the planted shell's read-back refuses, and no row holds that case |
| the independent comparison catches it | the honest child of the same operations, replayed under the plant beside the computation that keeps no memo, differs |
| the workshop catches it | it keeps no memo and refuses the file: `SESSIONWALK-CHAIN-BROKEN` |
| an honest shell catches it | a shell without the plant refuses the same file: `SHELL-LIVESESSION-TAMPERED` |

Two more points of his, both about what is not claimed. On the times: *The one thing I would not do is turn the
0.10/0.13 s container timings into a row. Keep them as development measurements. The Windows journal-flush cost
remains an explicit performance unknown.* They stay as the table above gives them: OBSERVED, one machine, no row. On
the amendments, their order confirmed: the build's changes first, then the exact files and hashes, then the two
entries written, then their commit placed before the build's. *Otherwise the amendment would describe a source
state that doesn't yet exist.*

**Deferred by the owner's ruling (2026-10-06), and not part of DESIGN-EVENT-0.** Recorded in his words, with nothing
added to them:

> **DEFER — batch-proposal independent reconstruction.**
> The verifier does not reconstruct VRDNP2 proposal bytes from admitted events or independently recompute the
> proposal digest. Doing so would introduce a second VRDNP2 writer into the verification path and is outside the
> present admission boundary. Reopen only if durable independent provenance of the original proposal bytes becomes
> a requirement.

His reason for recording it so: *That preserves the clean boundary and prevents this rung from quietly growing a
second language implementation.* It is not registered, it is not a row, and it is not a debt of this rung.

**Not yet shown.** What an admission costs on the host: a batch's records are flushed one by one, and what a flush
costs on Windows is not measured. The design tool sending a batch on the host, to a session sealed there: the gate's
row admitted the 60 in its own root; the tool has not been shown doing it.

**Grade.** DECLARED: the registration, the court's rulings, the two amendments, the ruling that defers. ESTABLISHED
(gate, here): the six rows, 242 in the gate, three passes identical, one of them with the host's records present;
the same on Python 3.14.0rc2, one pass. OBSERVED (the build container): the times. OBSERVED (the owner's host, one
run, off the gate): the design tool's loop over ADMIT-0 and the two heads. MEASURED (host): the registration's gate,
236 of 236, pushed; the built gate, 242 of 242, ten runs on nine trees, all pushed. After the tenth,
`git log origin/main` on the host names its commit (`11afebf`) as the remote's head. The trees differ in documents
only, but for the sixth, the seventh and the ninth, which each add one entry to the ledger. The fourth and fifth runs were on one tree. By the owner's predicate: FULL×2 here, and
FULL×2 on the host by its fourth and fifth runs.

**does_not_show.** That a compiler nets a design correctly: that is content time and is not certified. That two
builds of the shell agree. That the memo is right on a session the court does not replay: the workshop is the
standing check, and it is run when a session is sealed, not when it is designed. What an admission costs on the
host. That the host's two runs on one tree agree in bytes: their outputs were compared as printed. That the files
Git ignores were the same for both. That the host's runs agree beyond what the compact output prints. That a
proposal's bytes can be
rebuilt from its admitted events, or its digest recomputed by a verifier: none does either, by the ruling above.
That a model can write a design worth admitting. Anything about a second editor.

**Falsifier.** A red row among the six on a later run of either machine with the tree unchanged. A batch whose child
differs in head, content, spec or witness from the same operations admitted one at a time. A file that loads
standing inside a batch. A refused batch that leaves anything. A dry run that writes. An admission bound to a
preview that reaches another head. A session whose content under the memo differs from the computation with none.

## DESIGN-IR/DIFF-0 — the design text is the source language, and its compile to the canonical VRDNP2 change set against a parent world is one tree-owned function (preregistered `2baa42f3`; the round around it named before the build, `DESIGN-IR/DIFF-0a` `c414587d`; both pushed, `83b0261..5c8ad19`; built: five rows, 247 in the gate, every registered value reproduced; the gate passes here and on the host, FULL×2 there on one tree; pushed, `11afebf..c8b6a1f`; the owner's rulings after it registered and built into two of its rows, `DESIGN-IR/DIFF-0c` `38b51bed`)

```
  design/   a client: hands over the design's bytes, keeps them by id        content time, not certified
        │
        ▼   the exact bytes of a design, VERDANDI-DESIGN 0, at most 16,384
  shell design-compile --session S --design D          the certified shell, a command apart from the admission
        │   read as the language, or refused with its line
        │   statements in order over a copy of S's world ──► the design's TARGET
        │   the net difference, in VRDNP2's one order, or refused: nothing is approximated
        ▼
  standard output: the batch's bytes and nothing else      proposal = SHA-256 of the design's exact bytes
        │
        ▼   DESIGN-EVENT-0, as registered: dry run · binding · N ordinary edits, each with the id beside it
  shell design --proposal P

  verify/   an independent reference in Python ◄─ byte for byte ─► the shell's compiler
            the statements applied by the gate itself to the parent's bytes ◄─ content ─► the admitted child
```

**Why there is a rung.** DESIGN-EVENT-0 left one limit standing in its own entry: *what compiles a design into a batch
is content time and is not certified; a compiler that nets wrongly produces a batch that means something else, and
the seam admits what it is given.* Ghost G28 names it first. The compiler is `design/design.py`, a few hundred lines
of Python that replay the session themselves and net the difference. This rung is that limit and nothing beside it.

**The word, and the court (the owner, 2026-10-07).** With the host's gate FULL×2 by his own predicate, his word was
*take next*. Four questions were put to him, and he locked all four: *That is a very tight rung. I would LOCK all
four and resist adding a fifth theorem to DESIGN-IR/DIFF.*

| the question | locked | the owner's refinement |
|---|---|---|
| what is certified first | the compiler | *DESIGN-IR/DIFF first certifies that one bounded design representation compiles deterministically to the canonical VRDNP2 net change set against a specified parent authority.* Not the diff alone: *You already have a canonical diff language: VRDNP2.* Not persistent objects: *That is a different rung* |
| where the compiler lives | the certified shell, with an independent reference in the gate | *design/ is a client of the certified shell compiler, not the authority and not the court.* And: *admission does not become the compiler court.* Nothing under `verify/` reads `design/` |
| how provenance is answered | the proposal id commits to the design | *proposal_id = H(exact design bytes).* No member is added to the saved form. *If the original design bytes are not retained somewhere in the project, the ID is a commitment, not independently recoverable provenance.* No operation is attributed to a statement: *a separate semantic requirement* |
| readings and constraints | out, by name | *A reading is an observation of the current tool. A constraint is a claim with authority-bearing semantics.* Putting constraints in would make it two claims |

His wording of the claim, registered as given: *The current Verðandi design text is registered as the source
language, and its deterministic compilation to the canonical VRDNP2 net change set against a specified parent world
is one tree-owned function held by the court. Source constructs have no authority identity after admission.*

**His seven, and where the registration holds each.**

| the court establishes | held by |
|---|---|
| one language: the design statements as implemented | `designir-language`: a corpus of refusals at their lines, and the shell's verdict on every single-byte mutant of three designs against the gate's reference |
| one compiler: one tree-owned path produces the batch | `designir-fence`, by source |
| determinism: the same parent and the same design bytes give the same VRDNP2 bytes | `designir-compile`: two runs, the reference's bytes, and a digest registered before the compiler exists |
| semantic equivalence: the batch, admitted, is the world the design describes | `designir-equivalence`: the gate applies the statements itself to the parent's bytes, never through a change set, and compares content; six planted compilers that change the world, each caught twice |
| a refusal boundary: what cannot be said is refused, never approximated | `designir-language` for the codes; three planted compilers that approximate, in `designir-equivalence` |
| no object persistence | the child is ordinary edits with DESIGN-EVENT-0's envelope and nothing more; the workshop and the sealer verify it unchanged |
| no verifier reconstruction | `designir-fence`: the loader, the workshop and the sealer read no design, call no compiler and write no batch. The deferral of 2026-10-06 stands |

He named the fourth as the adversarial one: *Merely proving design text → VRDNP2 doesn't prove that the compiler
produced the right VRDNP2. You need a planted compiler mutation that survives syntactic validity but changes the
resulting world/diff, and the court must catch it.*

**The source language, pinned at the byte.** `VERDANDI-DESIGN 0`: the statements the design tool implements today.

| | |
|---|---|
| size | at most 16,384 bytes, at most 64 statements, at least one |
| lines | the bytes between LFs. A CR directly before an LF is not part of the line. Bytes after the last LF are a last line |
| line 1 | `VERDANDI-DESIGN 0`, with spaces and tabs at either end dropped |
| a comment | from the first `#` of a later line to its end. It may hold any byte |
| a statement | words separated by spaces or tabs, every byte of a word printable ASCII |
| the statements | `open CELL` · `open CELL CELL` · `close CELL` · `close CELL CELL` · `room CELL CELL` · `entrance CELL` · `paint CLASS R,G,B` |
| a cell | `X,Z`, decimals with no leading zero, inside the parent's level. Two cells are a rectangle's corners in either order |
| a room | at least three cells each way: a rim and an inside |

This is narrower than what the tool accepted by accident: it split on every blank Python knows and took a CR
anywhere. The pin is deliberate, and the statements are the tool's.

**What a design means.** The statements are applied in order to a copy of the parent's world. `open` writes floor to
its rectangle, `close` rock, `room` rock to the rim and floor to the inside, `entrance` floor to its cell, `paint`
one colour to a class. A later statement writes over an earlier one. What results is the design's **target**. The
change set is the net difference between the parent's world and the target, in VRDNP2's own order: cells row-major,
then the classes. A room is a statement. Once compiled there are operations, once admitted there are ordinary
edits, and nothing in a batch, an envelope or a session names a room.

**The refusal boundary.** Nine codes, first registered here, in the order the checks are made.

| code | when | names a line |
|---|---|---|
| `COMPILE-IO` | the design cannot be read | no |
| `COMPILE-SIZE` | more than 16,384 bytes | no |
| the loader's own | the session does not load | |
| `COMPILE-SESSION` | a journal, not a saved session | no |
| `COMPILE-PARSE` | a line that is not the language; a design with no statement, at its last line | yes |
| `COMPILE-RANGE` | a cell outside the level; a room under three cells each way | yes |
| `COMPILE-SIZE` | a statement after the 64th | yes |
| `COMPILE-BORDER` | a statement writes floor to a cell on the level's border | yes |
| `COMPILE-STAIR` | a statement writes to a stair cell. VRDNP2 opens and closes and has no stair | yes |
| `COMPILE-CAMERA` | the target leaves the camera's cell closed | no |
| `COMPILE-SIZE` | a change set of more than 4,096 operations | no |
| `COMPILE-EMPTY` | the change set is empty. A batch has at least one operation | no |

Every line is read as the language before any statement is applied. The compiler never emits part of a design,
never skips a statement it cannot honour and never clips a rectangle. There is one mode: the tool's `--no-predict`
goes with the tool's own compiler.

**The command.** `shell design-compile --session S --design D` writes the batch's bytes to standard output, and
nothing else, ending 0; or refuses, ending 2, with nothing there. It writes no batch file, no journal and no
session, makes no run directory, and leaves S as it was. As every command of the shell does, the run puts its line
in the run ledger and a refusal its record in the refusal log, and the compiler writes nothing else. The batch is
VRDNP2 as registered: the compiling shell's two
identities, S's head as the parent, the design's id, the count and the operations. Nothing in it depends on a
clock, a host, a path or a random value.

**The id.** The lower-case hexadecimal SHA-256 of the design's bytes exactly as they were read. Nothing is
normalised: a design saved with CR LF, another comment or one more space is another design with another id, though
it may compile to the same operations. His chain:

```
  exact design bytes
       ↓
  design digest
       ↓
  proposal id
       ↓
  admission envelope
       ↓
  ordinary session events
```

DESIGN-EVENT-0 already puts the proposal id beside every event a batch admits and seals it with the session, so
nothing is added to the saved form. *DESIGN-IR/DIFF-0 establishes what source produced this change, not why the
world should contain it.* One consequence is the session's own rule and not a new one: a session refuses a proposal
id already in its admitted history, so the same design bytes are admitted at most once in a history.

**What this does to DESIGN-EVENT-0's words.** That entry says canonicalising belongs to whatever compiles a design
*and never to the shell, which recognizes or refuses and rewrites nothing.* The registration reads the sentence as
one about the admission, where it stands: `shell design` rewrites nothing. His ruling in that court was that
canonicalising belongs in the design compiler and not in the authority or session layer. His ruling in this one
puts the compiler in the shell's program as a command apart from the admission. It is handed no batch and
reorders, nets and rewrites none. This is the one place where the two entries' words rub, and it is the owner's to
strike.

**The five rows, as registered.** 242 rows become 247 with the build.

| row | what it must find |
|---|---|
| `designir-preregistered` | the entry at its hash, the three bounds and the registered values; each amendment entry the build carries, unedited |
| `designir-language` | every case of the corpus ends in its code at its line with nothing on standard output; six accepted spellings compile to the plain form's operations under ids of their own; on every single-byte substitution, deletion and insertion of three designs the shell's verdict is the reference's, mutant by mutant |
| `designir-compile` | the shell's bytes are the reference's, for each design against each parent, and a second run writes them again; the id is the SHA-256 of the design's bytes; the session is unchanged and nothing is written; the registered design gives the registered id, count and digest |
| `designir-equivalence` | each batch, admitted by the admission as it stands, gives a child whose content is the content of the design's target; the workshop and the sealer verify it; the ten plants |
| `designir-fence` | by source: one reader of the design's bytes, one compiler, reached from its two commands alone, writing no file; nothing of the source language in the admission, the session, the loader, the workshop or the sealer; nothing under `verify/` reading `design/`; the reference used in these rows alone. By what was heard: every child that did not end 0 carries a registered code |

**The plants.** `shell design-compile-selftest --plant`, each on a design and a parent the court names because the
plant bites there. `shell design-compile` takes none.

| plant | what the planted compiler does | how it is caught |
|---|---|---|
| `entrance-dropped` | an entrance writes nothing | its bytes are not the reference's; its batch is admitted and the child's content is not the target's |
| `order-reversed` | the statements applied last to first | the same two |
| `rect-short` | a rectangle stops one column short | the same two |
| `paint-next-class` | a paint lands on the class after its own | the same two |
| `first-wins` | a cell once written is not written again | the same two |
| `net-stale` | the net is taken against the base world, not the parent's | the same two |
| `stair-skipped` | a write over a stair is left out | the reference refuses the design, `COMPILE-STAIR`; the planted batch is admitted |
| `border-clipped` | a rectangle is clipped at the border | the reference refuses, `COMPILE-BORDER`; the planted batch is admitted |
| `camera-buried` | the camera's rule is not applied | the reference refuses, `COMPILE-CAMERA`; the planted batch is admitted |
| `id-stripped` | the id is taken from the design with its comments and blanks removed | its bytes are not the reference's and its id is not the design's digest. It reaches the honest head: the world cannot catch it, and the court says so |

**Registered before the compiler exists.**

| | |
|---|---|
| the design | 93 bytes: `VERDANDI-DESIGN 0` · `room 6,3 16,10` · `entrance 6,6` · `entrance 11,10` · `open 11,11` · `paint floor 60,70,90`, each line ended by one LF |
| its id | `b08482b7f01d1209c0b0b97f27f7ab9d02cda97c05964dbfcd07a2e20ebbd3dc` |
| against the parent of head `73571153c2fc…391c` | 60 operations, a batch of 908 bytes |
| the batch's SHA-256 | `a9f117c423529a1022febbf54af47063f778954b38c33cd6c765706db1f6f0f5` |
| the target's content | `02e77707372883396ed8ff5ba967dac01e3606926216d4ce5e1c9af01e89e334` |
| the child's head | `c18a71f6af8d…1036`, DESIGN-EVENT-0's registered head |

The design is the gate's spelling of the owner's design of 2026-10-06. It is not a record of his keystrokes.

**Seen before the registration, and disclosed in it.** The shell's compiler does not exist. A reference compiler was
written in Python from the description and run against the shell as built, through its admission.

| seen | what it shapes |
|---|---|
| the registered design compiled to 60 operations and 908 bytes, and the existing dry run gave the registered head | the id, the digest and the content were computed by the reference; the head predates it. The registration is not blind in those |
| the 40 refusals and orders of the registered corpus, and its six accepted spellings, run through the reference: none differed | the corpus was read against the reference before it was registered, not after |
| a plant bites only on some designs and parents. The short rectangle gives the honest bytes on the registered design: the column it leaves out was rock already. On a parent with a history a net against the base restates the parent's own edits, and the admission refuses that itself, nothing to change, unless the design undoes the whole of that history | each plant is run where it bites, and the court does not claim otherwise |
| the admission admits a batch that closes the camera's cell, and a batch that opens a stair | those two rules are the source language's alone. The tool had them as refusals it predicted of the seam; the seam does not make them |
| the same design bytes offered a second time in one history are refused `ADMIT-DUPLICATE`; with one more comment line they are admitted | the id's one consequence, registered as the session's own rule |

**On the host (DANIELDILLBERG, output given 2026-10-07): applied.** 0137, 0138 and 0139 were applied and the gate
read `GATE PASSED`, rowset `aa94c886190510c7`, 242 rows / 0 fail / 0 skipped. The registration is in the host's
ledger and no row before it moved. The output ends at the gate: no push is in it, and none is written here.

**Pushed (output given 2026-10-07).** 0140 and 0141 were applied, the gate read `GATE PASSED`, rowset
`aa94c886190510c7`, 242 rows / 0 fail / 0 skipped, and the owner pushed. Git's own output:
`83b0261..5c8ad19  main -> main`. That range carries 0137 to 0141: the registration, the amendment and their
records. Both entries are public before anything of the rung is built.

**The owner's reading of the registration (2026-10-07).** *I would push 0138/0139 with only one substantive strike:
do not let the pre-registration accidentally promote the camera/stair rules into authority law. The entry currently
does a good job saying they are source-language rules only. Keep that.* So nothing was struck. Part by part:

| the part | his word | what he fixed with it |
|---|---|---|
| the command's boundary | LOCK | design bytes and a parent authority in, VRDNP2 bytes out: *No mutation, no admission, no persistence* |
| the compiler and the reference | LOCK | *one production compiler in the certified shell; one independent court implementation in `verify/`.* The deferral of 2026-10-06 *was specifically about reconstructing proposal bytes from admitted session events, not about an independent oracle for this new rung* |
| the equivalence | the theorem to watch in the build | three equalities, set apart: the same design and parent give the same bytes; the shell's output is the reference's; the design's meaning applied is the batch applied. *The third is the actual semantic theorem* |
| the camera and the stair | DEFER, and not into the authority | *the source language is narrower than the underlying authority language.* That is not a contradiction. No authority court is added to this rung |
| provenance | LOCK | the id says what source produced a change, which *prevents provenance from quietly becoming intent semantics*. Per-operation attribution *would be a fifth theorem in disguise* |
| constraints and readings | out | otherwise the rung is compiler correctness, constraint semantics and constraint witnesses at once |

The predicate he locked before the build, the first equality of bytes and the second of the world's content:

```
  Compile_shell(D,S) = Compile_ref(D,S)    AND    Apply(VRDNP2,S) = Target(D,S)
```

*Then the compiler mutation court attacks both sides independently.* And of the build: the decisive gate is not
whether the compiler produced a plausible batch but *whether a valid-but-wrong compiler can survive the byte oracle
or the direct semantic equivalence court.*

His verdict: *PUSH 0138/0139.* *I would make no fifth theorem, no constraint court, no authority camera/stair
amendment, no saved-form change, and no design-tool certification.* One question he carries forward, and rules is
not to be answered in this rung: *Should camera/stair validity be an authority invariant, or deliberately remain a
property of the design language?*

**The round (his second text, the same day).** *This is a good round to batch the seams that are prerequisites for
DESIGN-IR/DIFF-0, but I would keep the actual court count tight.* Its shape, as he drew it:

```
  DESIGN-IR/DIFF-0          ← main theorem
          │
          ├── BOUNDARY-0    ← refusal language
          ├── REPLAY-0      ← semantic application
          ├── ID-0          ← byte commitment
          └── CLIENT-FENCE  ← architecture

  supporting:
          ROUNDTRIP-0
          MUTATION-0
```

*I would register all six/seven together if the prereg can stay clean, but only make DIFF-0 the principal rung. The
others should either be named subcourts/amendments or very small adjacent rows, not seven new claims.* They are
registered as one amendment, `DESIGN-IR/DIFF-0a` (`c414587d`), before anything is built. It adds no claim and no
row: each subcourt is a part of a row this rung already registered.

| the subcourt | his predicate | where it is held | what the amendment adds |
|---|---|---|---|
| BOUNDARY-0 | `Compile(D,S) = REFUSE(code)`, and never a partial result. *The compiler's refusal boundary is part of the language, not merely error handling* | `designir-language`, and the three plants that approximate | two statements on one line; for five codes, the refused statement last and first among statements each admissible alone, with nothing on standard output either way |
| REPLAY-0 | `Apply(Compile(D,S),S) = Target(D,S)`. *I would not build a second replay system* | `designir-equivalence`: the admission's own replay against the gate applying the statements | no-op writes; overlapping rectangles; a later statement over an earlier; a rectangle's corners in four orders; a class painted twice, and painted its own colour; every statement kind in one design; net-zero; and an eleventh plant, `net-short`, for this equality alone |
| ID-0 | `ID(D₁) = ID(D₂)` iff `D₁ = D₂` byte for byte. *Same semantics ≠ same proposal ID* | `designir-compile` | the registered design on two parents carries one id; LF against CR LF, a blank, a comment added and changed, two statements exchanged, a final LF dropped, every accepted single-byte mutant |
| CLIENT-FENCE-0 | `design.py → shell compiler → VRDNP2`, never `design.py → VRDNP2` | the design tool's own checks, off the gate | the tool's batch is the compiler's bytes; the tool proposes what a stand-in compiler writes; its source holds no writer and no netting; four plants made from the tool |
| ROUNDTRIP-0, supporting | design, compile, batch, admit, world, inspect | REPLAY-0 on the gate; the tool's own check of `inspect` off it | nothing on the gate |
| MUTATION-0, supporting | *does the test suite actually detect deliberately introduced faults?* | a campaign off the gate, as mutation testing has been here | his twelve targets; aimed at checks no row notices, not at a count |

Five things the amendment says plainly.

- **One plant is for the second equality alone.** He wrote that this seam is distinct from byte equality because *a
  compiler can emit the same wrong batch as the reference compiler.* The ten registered plants do not show that: a
  planted compiler disagrees with an unplanted reference, so the byte oracle catches each first. `net-short` leaves
  the last operation out of the net, and for that one case the gate's reference is given the same omission. The
  bytes agree, the batch is admitted, and the child's content is not the target's. So each equality is shown to
  catch what the other cannot: `id-stripped` by the bytes alone, `net-short` by the content alone. Tried before the
  entry as a batch of 59 of the registered design's 60 operations: admitted, another content.
- **The client fence is not a row.** He wants the tool held from becoming a second compiler: *otherwise the nice
  compiler court can exist while the actual content-time client silently becomes a second compiler.* Two of his
  locks leave it one place. The registration forbids anything under `verify/` reading `design/`, and he ruled no
  design-tool certification. So it is the tool's own checks, with plants made from the tool. Making it a row would
  reverse a lock of the court, and that is his to rule.
- **ID-0's iff, graded.** Equal bytes give an equal id on any parent: that is determinism, and it is shown. That
  different bytes cannot share an id rests on SHA-256 and is shown only for the pairs the court holds.
- **What the second equality is not independent of.** The target is taken by the gate's own reading of a statement.
  A misreading shared by the compiler and the reference is caught by neither equality.
- **The added cases were run through the reference first.** Each ended as the amendment says. No row has run them.

His deferred list, registered with it: persistent object identity; constraints; the camera's and the stair's rules
as authority invariants; statement-level provenance; independent VRDNP2 reconstruction, which is not to come back
*as a "test"*; incremental or delta verification; a model; a random or property-generated corpus; a design history
kept apart from the session's. His closing: *The strongest preparation before pushing is therefore not more theorem
surface.* What matters is that the court kills a compiler that is *syntactically valid, produces a valid VRDNP2
batch, agrees with its own digesting, but produces the wrong world.*

The second text cites two outside pages, for differential testing and for mutation testing. They are its
citations. They were not opened here, and nothing in the amendment rests on them.

**Out, by name.** Readings: they stay the design tool's views. Constraints: their own court. Persistent objects, a
relation, an identity that outlives admission: a later rung. A diff between two sessions. An operation attributed
to a statement. A batch rebuilt from events. The camera's and the stair's rules as the authority's.

**What it owes the earlier rungs.** The build changes the shell's sources, so REASON-COURT-0's pins on them move:
an amendment entry with its own hash, written after the build and committed before it, as before. The mint
register's pins are not expected to move. No row of an earlier rung changes its text, and if holding one needs more
than a pin moved, the build stops and the owner rules. (It did, in two rows: see the build, below.)

**Grade.** DECLARED: the word, the court's four locks, the registration, his reading of it and the amendment.
OBSERVED (the build container, one sitting, before each entry): the reference's results, the ten planted behaviours
through the existing admission, and the amendment's added cases. MEASURED (host): the gate with the registration
applied, 242 of 242, one run, and with the amendment applied, 242 of 242, one run; pushed. At registration nothing
of the rung was ESTABLISHED: there was no compiler in the shell and no row. The build's grade is its own, below.

**does_not_show.** Anything about a compiler that is not built. That the reference's reading of a room is what a
designer means: the compiler and the reference are two programs written from one description by one hand. That a
model can write a design worth admitting.

**Falsifier (of the registration).** A registered case the built reference decides otherwise. A registered value
the built compiler does not reproduce. A plant that cannot reach what it is said to catch. A pin of an earlier rung
that the build has to move without an amendment.

### The build (2026-10-07): the compiler in the shell, five rows, 247 in the gate

```text
   D, S ─────► shell design-compile ─────► batch ─────► shell design ─────► child session
     │                                      ║ bytes                           ║ content
     ├──► the gate's reference (Python) ───► batch′       designir-compile    ║
     └──► the statements applied by the gate to S's level and tiles bytes ───► target     designir-equivalence

   history   was ─► is, in the entries       identity   a file's hash, in the pins       behaviour   a row passes
             three layers, kept apart; none stands in for another
```

**What was built.** `shell/designcompile.rs`, new, and in `shell/main.rs` one module line and one arm: thirty
lines. `shell design-compile --session S --design D` reads the design's bytes and the saved session, and writes the
batch to standard output and nothing else, or refuses with a code and the design's line and writes nothing there.
It reads the session through the loader's own verified load and writes the batch with DESIGN-EVENT-0's own writer.
It admits nothing. `shell design-compile-selftest` is the same run with one of eleven plants, or the court in
process over every single-byte mutant of a design.

**The registered values, reproduced.** They were registered before the compiler existed. The compiler gave them on
its first run.

| registered | value | reproduced by |
|---|---|---|
| the design's id | `b08482b7…ebbd3dc`, the SHA-256 of its 93 bytes | the batch's proposal line |
| its change set against the registered parent | 60 operations, 908 bytes, `a9f117c4…f0f5` | `shell design-compile`, and the gate's reference, byte for byte |
| the target's content | `02e77707…e334` | the gate applying the statements to the parent's bytes; and the admitted child |
| the child's head | `c18a71f6…1036` | `shell design` admitting the compiled batch |

**The five rows.** 242 rows become 247. Rowset `389da490e1cfb6aa`.

| row | what it holds | how much |
|---|---|---|
| `designir-preregistered` | the entry and DIFF-0a at their hashes; the bounds, the registered design and the eleven plants as the shell holds them; the two amendment entries the build carries; the amendment chain and its origin | four plants on the chain's own checks |
| `designir-language` · BOUNDARY-0 | each refusal at its registered code and line, exit 2, nothing on standard output, one record, one ledger line, nothing left; what the language accepts compiles to the plain form's operations under an id of its own; in process, the shell's verdict on every single-byte mutant of three designs is the reference's | 70 refusals; 8 accepted forms; 114,432 mutants, 5,800 of them accepted |
| `designir-compile` · ID-0 | the shell's bytes are the reference's, and a second run writes them again; the header is the session's head, the design's digest and this shell's two identities; one id on two parents; a byte's difference is another id | 16 designs on 4 parents; 8 designs that differ in a byte; every accepted mutant |
| `designir-equivalence` · REPLAY-0 | each batch admitted; the child's content is the target's; the workshop and the sealer verify each child; every admitted event is an ordinary edit carrying the design's id; the registered design against its own child is `COMPILE-EMPTY`; the same bytes twice in one history are `ADMIT-DUPLICATE` | 16 children; 11 plants |
| `designir-fence` | the compiler's source spawns, connects, times and writes nothing; one function reads the design; the checks stand in the registered order; reached from its two commands alone; nothing else holds the language; no file under `verify/` reads the design tool's folder; the reference is these rows' alone; every ending heard carries a registered code | 75 endings: 70 in the language court, 5 in the semantic one |

**The plants.** Each on a design and a parent where it bites.

| plant | where | the bytes | the world |
|---|---|---|---|
| `entrance-dropped`, `order-reversed`, `paint-next-class`, `first-wins` | the registered design, the registered parent | not the reference's | the child's content is not the target's |
| `rect-short` | the second design, on the registered design's child. On the registered design it writes the honest bytes: the column it leaves out was rock already | not the reference's | not the target's |
| `net-stale` | a parent that closed one cell; a design that opens it and closes another | not the reference's | not the target's |
| `stair-skipped`, `border-clipped`, `camera-buried` | a design the reference refuses with its code, and so does the compiler without the plant | a batch is written, and the admission admits it | the language's boundary, not the authority's, is what refuses |
| `id-stripped` | the second design, which holds a comment | not the reference's; the id is not the design's digest | the honest head and the target's content: the world cannot catch it |
| `net-short` | the registered design; the gate's reference is given the same omission | the planted reference's, 59 of 60 operations: the bytes cannot catch it | not the target's |

So each equality catches what the other cannot, as DIFF-0a required: `id-stripped` by the bytes alone, `net-short`
by the content alone.

**The stop clause, met twice.** The registration says: *if holding an earlier row needs more than a pin moved the
build stops and the owner rules.* It needed more in two rows of DESIGN-EVENT-0, both written as if that rung were
the last.

| row | what it held | why it fails with this build | what it holds now |
|---|---|---|---|
| `designevent-preregistered` | each pin REASON-COURT-0a moved is the file as built, and that entry names the built file's hash | the command changes `shell/main.rs`, one of the five. The entry is never edited, so it names a hash the file no longer has. No pin moved can hold the row | REASON-COURT-0a against the hashes that entry names; the built file through the amendment chain |
| `designevent-fence` | its six rows are the gate's last six | five rows follow them | its six rows are the six that follow the 236 before them |

The owner was told of the first when it was found, and of the second before anything was cut. Nothing was cut
until he ruled.

**His three texts, and the rulings (2026-10-07).** Recorded as he brought them; where a text met the pushed
registration, what was put to him is recorded too.

- *The first* names the flaw: the row *binds an amendment to a timestamp ("today") instead of to a semantic
  invariant ("what the amendment said")*, and *this is not a content problem — it's a binding semantics problem.*
  It takes the chain, asks that it be named as a convention so that later amendments inherit it, considers binding
  to what an amendment describes in place of binding to bytes and defers it, and proposes splitting the row in two.
  It also asks whether host records are piling up as duplicate state, and whether a sample of the mutants would do.
  Put to him in answer: a sixth or seventh row is against the registered 247 and against DIFF-0a's *no row added*;
  the second of the two rows would check a described change, the binding the same text defers; the half that must
  hold on every gate is already held by `reasoncourt-fence` and `mintwatch-fence`; and the mutant court is
  registered as every single-byte mutant, so it cannot be sampled without breaking a pushed entry.
- *The second* agrees to build with the chain, named, and says: *The fork stays deferred.* It asks that the
  inheritance rule be written into the entry (*No additional ruling required for subsequent links*), that the
  mutant court's cost be reported without sampling it, whether the hashes should be captured after the build in a
  companion entry, and whether a row could declare earlier host records superseded (*declare supersession, don't
  delete*). It then asks one question: does *intent verification*, as distinct from byte verification, change the
  case against the fork? The answer given: the distinction is real, and the earlier answer's reason was wrong.
  `reasoncourt-fence` holds identity and nothing of intent. Intent is held here by the rung's own rows: without
  the arm, the command does not exist and every case of three rows fails. What no row catches is a byte changed
  where nothing looks, and for `shell/main.rs` that is recorded as a fact about two committed files. The
  inheritance rule went into REASON-COURT-0b, since REASON-COURT-0a is pushed and never edited. The companion entry
  is not needed: an amendment is written after the build, by rule. The supersession row was not taken: it is a
  sixth row, and each DRIFT-0 sitting is its own record by that rung's design.
- *The third* sets the whole in a formal model and rules, in this order.

| ruling | his word | the form he gave it |
|---|---|---|
| 1. the amendment chain | accept | `was₍ᵢ₊₁₎(f) = isᵢ(f)`; REASON-COURT-0a immutable. *A is not an exception to the invariant. It is the invariant correctly stated.* |
| 2. the fence's anchor | accept | the six rows *immediately following* the 236. A block meant as fixed history is anchored to an immutable predecessor, not to the ledger's end. *This is not a weakening*: a suffix predicate becomes a historical-position predicate |
| 3. the stair parent | accept | `C₁ = C₀ ∪ {p₄}`. Record the surviving planted mutant and the reason. *Do not expand beyond the demonstrated counterexample* |
| 4. a semantic diff | reject, for this rung | it adds a trust boundary the existing obligations do not call for. The rung needs byte identity and exercised behaviour |
| 5. permanent extra rows | reject | none of the three corrections needs one |

His principle for all three: ***history is immutable; state may evolve; transitions must preserve provenance.***
And his closing instruction: *Do not invent a fourth proof layer merely to resolve an ambiguity that the three
existing layers already settle.*

**The amendment chain, a law now, and its origin** (`REASON-COURT-0b`, `d51b4d20`).

| link | `shell/main.rs` had | has |
|---|---|---|
| REASON-COURT-0a | `c6d2aaa2…` | `d5324e62…` |
| REASON-COURT-0b | `d5324e62…` | `8db2d8ee…`, the built file |

Each link starts where the one before it ended, and the last is the built file's. `shell/designcompile.rs` is
added (`123c1584…`). The other 56 pins stand. A later link needs an entry of its own and no new ruling.

He asked whether the tree already realized his relations, and for the smallest correction where it did not.
Identity and behaviour were held as built, and history between named links once the row read the chain. **One
relation was held by no row:** that every pin is REASON-COURT-0's own or is reached from it by named links. A pin
changed together with its file, and named by no entry, passed every row. The correction is inside the history
layer and adds no row: REASON-COURT-0b registers the digest of the 56 pins REASON-COURT-0 found (`99d0d92e…ae3e`),
and `designir-preregistered` holds that today's 58 pins with every link undone are those 56. The digest was
checked here against the gate's own table at the commit that built REASON-COURT-0: equal. Four plants on these
checks are refused: a link that does not start where the one before it ended, a chain that stops before the built
file, a pin moved that no link names, and a link left out of the table.

One fact is local to the transition and is recorded in the entry, not made a row: the built `shell/main.rs`, less
the three lines that declare the module and the twenty-seven of the arm, is byte for byte the file
REASON-COURT-0a named. A row could hold that only until the next amendment moves the pin.

**DESIGN-IR/MUTATION-0, off the gate.** One sitting in the build container, scripts outside the repository. One
defect at a time in the built compiler and its arm; the rung's rows run against each. His instruction was to aim
at the surviving class and not at the count, so the table is by class.

| class | how many | which |
|---|---|---|
| caught by a row that runs the compiler | 85 of 94 | his twelve targets among them: an operation dropped; the order reversed; a rectangle's bound changed; a paint's class changed; the first write winning; a stale parent (two forms); a wrong id (two forms); a wrong count; each refusal skipped; a refusal clipped; an invalid camera, stair or border operation accepted; the batch's order altered |
| caught only by the last row's reading of the source | 4 | the parser's own size check (the command's check covers it); the bound of 4,096 operations (registered as unreachable on a level the kernel takes); `design-compile` taking a plant, and the selftest taking any plant's name (no row can run a usage refusal: it has no registered code) |
| survived, equivalent by reading | 5 | the printable-ASCII check and the word split, which cover each other; the colour's digit count, covered by its bound of 255; paint's word count, held on both of its sides |
| survived, a hole | 1, closed | a compiler that takes only floor under the camera refuses every design made from a stair. No parent of the court stood on one. The fourth parent catches it, in two rows |
| second order: a covered check and its cover, taken out together | 3 of 3 caught | the two size checks; the printable check and the split; the colour's bound and its digit count. Paint's two sides together were among the 85 |
| not a mutant | 1 | a replacement of mine for *a stale parent* changed nothing reachable. It is named, withdrawn, and replaced by two that are caught |

- **Four defects were caught by no named case.** The border's first row and its last row not held, the level read
  one row short, and paint taking a fourth word were each caught only by the court of single-byte mutants. The
  named corpus alone would have passed all four. That is the answer to sampling the court: what it catches is not
  where a sample would look.
- **One candidate case was taken out again.** A case for paint with a fourth word was written when that defect
  looked likely to survive. The mutant court caught the defect without it, so the case went. The corpus grew by
  the stair parent and nothing else.
- **Not reached by any row:** a failed write to standard output ends 1 with no code.
- **The control passes:** with nothing changed, all five rows.

**The design tool, a client now (off the gate, no row).** `design.py` hands the design's bytes to
`shell design-compile`, keeps the batch it writes, and keeps the text under its id in `designs/`. Its own parser,
compiler and writer are gone, and `propose --no-predict` with them. A design's refusal is the shell's
(`SHELL-COMPILE-*`). A design that changes nothing is now a refusal, `COMPILE-EMPTY`, where it was a note.
`design/test_design.py` holds seventeen checks. One is CLIENT-FENCE-0, and four are its plants, each a changed
copy of the tool:

| a tool that… | caught by |
|---|---|
| computes its own difference (and, for the fence's design, writes the compiler's very bytes) | the stand-in compiler alone, and the source reading |
| rewrites the compiler's result | its bytes are not the compiler's; the shell refuses the preview |
| never calls the compiler | its bytes; the call that was not made; the stand-in; the source |
| admits without the preview's binding | bytes changed after the preview were admitted |

The first row of that table is why the stand-in is there, as DIFF-0a said it would be: on that design a tool that
nets for itself is byte for byte an honest one. The tool's side of ROUNDTRIP-0: after an admission, `inspect`
shows the room's rim, inside, entrance and colour as the design said them, typed by hand in the check.

**What it costs, a development measurement.** The build container, two cores, one sitting, taken by a script
outside the repository: the three rows that run the compiler take about 37, 17 and 16 seconds. No part of the
claim, not a row, and nothing about the host.

**Outside pages, found by search at the owner's word** (*websearch as you go for elegant/pioneering hardenings*).
Paraphrased and attributed. One limit of REASON-COURT-0b names the first as prior art; nothing else in a row or
an entry rests on any of them.

- *Supply-chain attestation.* A page explaining the in-toto framework (docs.devguard.org) describes each step
  recording the hashes of what it consumed and what it produced, a verifier matching one step's products to the
  next step's materials, and the limit that this shows files passed unchanged and nothing about whether a change
  was intended. That is the amendment chain and its limit. The law is carried here, not discovered here.
- *Mutant subsumption.* Parsai and Demeyer, *Dynamic Mutant Subsumption Analysis using LittleDarwin* (arXiv
  1809.02435), as fetched: a mutant that another always carries with it adds no information, and a score counted
  over such mutants flatters a suite. So the campaign's table is by class and is not a score.
- *Higher-order mutants.* Wong, Meinicke, Chen, Diniz, Kästner and Figueiredo, *Efficiently Finding Higher-Order
  Mutants* (arXiv 2004.02000), as fetched: two changes together can behave unlike either alone. Here it runs the
  other way: two checks each cover the other's removal, so each survivor is equivalent alone and the pair is not.
  Each pair was taken out together and was caught.

**Grade.** DECLARED: the three texts, the rulings, the law, the principle. ESTABLISHED (gate, the build container):
the five rows, 247 in the gate, three passes identical, one of them with the host's records present. OBSERVED (the
build container, one sitting): the mutation campaign; the tool's own seventeen checks; the times; the origin's
digest against the earlier commit. When this was written the build had not run on the host. It has since: see the
next part.

**does_not_show.** Equivalence for every design: it is shown on the court's sixteen and on the single-byte mutants
of three. That the reference's reading of a statement is what a designer means: a misreading shared by the
compiler and the reference is caught by neither equality, and HERMENEUTICS-0 is registered for that. That a batch
from another editor obeys the camera's and the stair's rules: they are the source language's. That a hole no
mutant was written for is absent. That the changed files are right: a pin names a file. That no other row holds a
pin against today: MINT-WATCH-0a's pin on `verify/livesession.py` is still held that way, and is untouched because
that file does not change. That two builds of the shell agree. What a compile costs on Windows.

**Falsifier.** A design and a session that compile to two byte sequences. A batch the compiler writes whose child
is not the statements applied to the parent's bytes. A planted compiler from the registered eleven that the two
equalities pass. A pin that is the built file's and is neither the origin's nor reached from it by a named link.
The host's gate not reading 247 rows with rowset `389da490e1cfb6aa`.

### On the host, and the owner's fourth text (2026-10-08)

```text
   CHAIN on the host ── read first ──►  valid?  ── no ──►  the chain is invalid there. Nothing is compared.
        │ yes
        ▼
   rows the same by name and order · the printed log the same · the registered values reproduced on each
        │
        ▼
   a difference now is one of reconstruction or of platform, not of history
```

**The host's runs of the 247-row gate (DANIELDILLBERG).** Each read `GATE PASSED`, rowset `389da490e1cfb6aa`,
247 rows / 0 fail / 0 skipped. The range is Git's own output.

| run | the tree it ran on | its output given | pushed |
|---|---|---|---|
| 1 | the tree of the 242-row gate's tenth run with 0145, 0146 and 0147: the two amendment entries, the build, its record. Git's id of it: `247defb4088531a6c0116991ee792dba6635ff21`, with a status that lists nothing | 2026-10-08 | not in its output; with run 2's |
| 2 | the same tree: the next command after run 1. The same id and the same empty status after it | 2026-10-08 | `11afebf..c8b6a1f`, which carries 0145 to 0147 |

So REASON-COURT-0b and DESIGN-IR/DIFF-0b are pushed, and are registered in the project's sense. The design tool's
own checks ran there too, between the second run and the push: `DESIGN TOOL PASSED  17 checks / 0 fail`, the
client fence and its four plants among them. That is the first time the tool ran on the host as a client of the
shell's compiler. It is content time and no row.

**FULL×2 on the host, by his predicate.**

| | TreeID₁ ? TreeID₂ | GateOut₁ ? GateOut₂ | FULL×2 |
|---|---|---|---|
| host, runs 1 and 2 | `==`: Git's id of the commit's tree, `247defb4…`, taken before the first run and after the second, with a status that lists nothing both times | `==`, as printed: the two outputs he gave, compared here line by line, 250 lines each | TRUE |

**The host reconstruction, read by the protocol he ruled.** The precondition first, then the comparison.

| step | what was read | result |
|---|---|---|
| the chain on the host | `designir-preregistered`, `designevent-preregistered`, `reasoncourt-fence` and `mintwatch-fence` in both of the host's runs: every link starts where the one before it ended, the last is the built file's there, and today's pins with every link undone are the origin's | valid. (The layout comparison in `designir-fence` is DIFF-0c's and was not yet in that tree) |
| the rows | 247 names in one order on both machines, rowset `389da490e1cfb6aa` | the same |
| the logs | the host's printed output against the build container's log, line by line; with line ends as LF the host's text has the container log's SHA-256, `dc96d377…` | the same, as printed |
| the registered values | the design's id, its 908 bytes, the target's content and the child's head are literals in the rows, and the rows pass on each machine | reproduced on each |

The trees are not the same tree: the host's holds its records, and Git's id of it is not the container's
(`c8bac9d4…`). What is the same is what the gate printed and what the rows hold. The compact output prints a row's
name and whether it passed; the rows' counts were printed by neither host run.

**His fourth text.** It rules on three candidates that had been put to him in private, and on two suggestions. Its
distinction: *DIFF-0 should certify a state transition, not grow a general-purpose provenance system.*

| item | his ruling | where it rests |
|---|---|---|
| a ledger head: a commitment over the ledger's entries, so a later ledger can be shown to extend an earlier one | **DEFER** | nothing built. It answers a later question than this rung's |
| validating every compile at content time against the statements applied to it | **REJECT** for this rung; kept as a ghost | G29. It would collapse the thing compiled and the court that judges the registered claims |
| the registration's instrument as a layout | **ACCEPT**, no new row | `designir-fence` |
| the origin's digest | **ACCEPT**, as a projection | `designir-preregistered` |
| a chain-validity precondition before the machines are compared | **ACCEPT**, as a protocol and not a row | the table above; every later host run that is compared |
| a triple-write or meta-audit, as his table names it | **DEFER** | nothing built; wait for a first independent host result |

They are registered as `DESIGN-IR/DIFF-0c` (`38b51bed`), an amendment written with the host's output in view and
blind in nothing. It adds no claim and no row.

**The four relations, in his words no fifth.**

| relation | his form | held by |
|---|---|---|
| historical continuity | `was₍ᵢ₊₁₎ = isᵢ` for every link | `designevent-preregistered`, `designir-preregistered` |
| origin closure | `H(Canon(Orig(Pₜ))) = RSN_ORIGIN` and `|Orig(Pₜ)| = 56` | `designir-preregistered` |
| behavioural realization | every registered row passes | the gate |
| declared-transition completeness | `Δ_D(S₀,S₁) = N_Δ(A)` | `designir-fence` |

An independent reconstruction on another machine is the test that the four are realized. It is not a fifth.

**What DIFF-0c built, in rows that exist.**

- *The layout.* The domain `D` is the files REASON-COURT-0 holds: 41 Rust sources under `kernel/`, `shell/` and
  `workshop/` and 17 sealers under `verify/`. `S₀` is the origin projection, `S₁` the files on disk. The fence
  holds both inclusions: no file of `D` differs from the origin that an amendment does not name as changed or
  added, and no amendment names a file that does not differ. Today that is seven files. Three plants on the same
  comparison are refused: a file changed that no amendment names, a file added that none adds, an amendment naming
  a file that did not change. Tried against the disk here, outside the gate: a line added to a workshop source,
  and a stray source under `shell/`, each turned the fence red with the file's name.
- *The origin as a projection.* The formulation his text corrects was not the tree's: the tree already undid the
  links before digesting. What the ruling adds is the count, held explicitly, and the name. Today's 58 pins,
  every named link undone, are 56 files that digest to `99d0d92e…ae3e`.
- *His qualification, a condition of the entry:* the origin's digest anchors identity and history and does not
  establish meaning. It commits to a set of pins. What those files do is the courts' to show.

Said plainly in the entry: over `D` the layout relation follows from the chain, the origin and the pins'
identity where all three hold. The fence now holds it directly, against the files and not against the pin table.
Outside `D` — the gate itself, the ledger, the registers, the design tool, the documents — the gate keeps no
origin. There a transition is shown by Git's own comparison of two commits, a fact of that transition. For this
rung's build that comparison lists seven files, and the registration's instrument names each of those places and
no other.

**The mutation campaign, in his reading.** He writes the campaign's classes as a partition, `M = M_C ⊎ M_F ⊎ M_E ⊎
M_H`: caught by a row that runs the compiler, caught only by the fence, equivalent, a hole. `M_F` is not empty:
four defects reached no behaviour and were caught only by the fence's reading of the source. So the fence is not
redundant with the rows that run the compiler. And the four caught only by the single-byte court are, in his
words, the strongest argument *against replacing the court with sampled named cases*.

His last word on the rung: *I would stop adding architecture here.*

**Grade.** DECLARED: the fourth text and its rulings; the protocol. ESTABLISHED (gate, the build container): the two
rows as DIFF-0c changes them, 247 in the gate, three passes identical, one of them with the host's records
present. MEASURED (host): the built gate, 247 of 247, two runs on one tree, FULL×2 by his predicate; pushed
(`11afebf..c8b6a1f`). OBSERVED (the owner's host, one run, off the gate): the design tool's seventeen checks.
OBSERVED (the build container): the host's printed output compared with the container's log.

**does_not_show.** That the host and the build container hold the same tree: they do not, and the comparison is of
what the gate printed. Anything about a file outside the layout's domain. That the pinned files are right. That
DIFF-0c's two changed rows pass on the host: they have not run there. What a compile costs on Windows: the host's
output carries no time.

**Falsifier.** A file of the domain that differs from the origin and that no amendment names, with the fence
passing. A host run in which a chain row fails and the machines are compared all the same. The host's gate, with
DIFF-0c applied, not reading 247 rows with rowset `389da490e1cfb6aa`.

## HERMENEUTICS-0 — the meaning of the design language, fixed apart from the two programs that compile it (preregistered `22d52d02` and pushed, `5c8ad19..11afebf`; not built; its condition is met: DESIGN-IR/DIFF-0 is built, courted and FULL×2 on the host; it waits for the owner's word)

```
  the owner's court ──► one reading, six rulings, four laws        ratified, 2026-10-07
        │
        ▼
  literal targets, typed by hand        ten designs on the registered parent · the cells that change, or the refusal
        │                               data in the entry · computed by no program
        ├──────────────► the shell's compiler      held to them
        └──────────────► the gate's reference      held to them

  DESIGN-IR/DIFF-0:   Compile_shell = Compile_ref        the two programs agree
  HERMENEUTICS-0:     Meaning_court = Target_owner       and never  Meaning_court = Compile_shell
```

**Why there is a rung.** DESIGN-IR/DIFF-0's amendment says of its own predicate that a misreading of a statement shared
by the compiler and the reference is caught by neither equality: the target there is taken by the gate's own
reading. The owner named the layer that belongs to (the declared section in
[`docs/ROADMAP.md`](../docs/ROADMAP.md)), and his later text asked that it be registered as something that can
redden: *an empty `HERMENEUTICS-0` registration would be weaker than registering a small semantic corpus.* *Not a
third compiler. Not semiotics. Not a general interpreter.*

**The trigger.** His second text had said: register an interpretive court only if an ambiguity appears that DIFF-0
cannot resolve. Six readings had been decided by DESIGN-IR/DIFF-0 by inheriting them from the design tool, with no
court. Those are the six cases.

**The court (2026-10-07), as it went.** It is recorded as it went, because the rung's evidence is his ruling.

| | what was put to him | his answer |
|---|---|---|
| Case 1 | where the three rules are judged: as registered; all on the target; all where a statement writes; underspecified. Each drawn as a grid | *As registered.* His own ruling |
| Case 2 | `open` on a stair: refused; a no-op; the stair becomes floor; underspecified | he asked for a web search on each question *for the wisest path*, *elegant*, combining theorems and design styles |
| Cases 3, 4 | `entrance`; `room` over floor on its rim | no preference |
| then | one reading that covers all six, drawn from outside sources, with a recommendation for each remaining case, the four laws, and a corpus | ratified, all four parts: the reading; LOCK on all five; the laws as theorems; the six cases and three more |

So one case is his own ruling and five are his ratification of a recommendation he asked for. The recommendation
was written by the hand that wrote the gate's reference. The entry says that as its first limit.

**The reading he ratified.**

| | |
|---|---|
| a statement | a finite partial map from targets to values, the same on every parent. The targets are the level's cells and the five classes |
| `open R` | floor to every cell of the rectangle R |
| `close R` | rock to every cell of R |
| `room R` | rock to the cells on R's rim, floor to the cells inside it |
| `entrance C` | floor to the one cell C |
| `paint K V` | the colour V to the class K |
| a design | its statements' maps composed in line order, the later winning |
| its target on a parent | the parent with that map laid over it. Everything the map does not name is the parent's, the stairs among it |
| the change set | the targets whose value in the map is not the parent's. VRDNP2 encodes that. It is an encoding of a difference and not part of the meaning |
| the static guard | no statement may give a frozen cell a value other than its own. The border is frozen at rock; a stair is frozen at itself, and the language has no value for a stair. Judged statement by statement |
| the state guard | the target may not leave the camera's cell closed. Judged once, on the target |
| the encoding's limit | a design whose change set is empty has a meaning, its target is its parent, and has no batch. `COMPILE-EMPTY` is the compiler saying it has nothing to write |

It says in other words what DESIGN-IR/DIFF-0's entry says in prose. It is ratified as the same meaning and makes no
successor language. If the two are ever found to differ, that entry is not edited: the owner rules the difference.

**The six rulings.** Each is LOCK. No case was found underspecified, and none is deferred.

| case | LOCK | not supported |
|---|---|---|
| 1. where the rules are judged | border and stair where a statement writes; the camera on the target | all three on the target; all three where a statement writes |
| 2. `open` on a stair | refused: a stair is frozen | a no-op because a stair is walkable, which would make `open` the one statement whose meaning depends on what was there; the stair becoming floor, which lets a design destroy what no design can restore |
| 3. `entrance` | one opened cell: `open` under another name | an entrance that must join floor. That is a relation between spaces, and belongs to a court of constraints |
| 4. `room` | rim rock and inside floor, whatever was there: floor already on the rim is closed | a rim that keeps its openings, which would depend on what was there |
| 5. `paint` | the whole class, one colour | a blend with what was there |
| 6. a design that changes nothing | refused by the compiler, its meaning intact | an accepted compile that writes nothing |

**The corpus.** Ten designs on the registered parent (head `73571153c2fc…391c`, the witness level, 48 by 32, the
camera at 28,28). Each is the line `VERDANDI-DESIGN 0` and its statements, every line ended by one LF. The targets
were typed by hand from the rulings and the parent's cells. Neither program produced them.

| | the statements | the literal target | shown by the reference before the court |
|---|---|---|---|
| H1a | `close 28,28` · `open 28,28` · `close 27,28` | rock at 27,28; nothing else | run and read |
| H1b | `open 0,27` · `close 0,27` · `close 27,28` | refused, `COMPILE-BORDER`, line 2 | run and read |
| H2 | `open 7,26` · `close 27,28` | refused, `COMPILE-STAIR`, line 2 | run and read |
| H2′ | `close 34,28` | refused, `COMPILE-STAIR`, line 2 | never run |
| H3 | `entrance 40,29` | floor at 40,29; nothing else | run and read |
| H3′ | `entrance 11,24` | floor at 11,24; nothing else | never run |
| H4 | `room 20,24 26,28` | rock at fourteen cells: 21 to 25 of row 24; 20 and 26 of row 26; 20 to 26 of row 28. No cell becomes floor | passed through a check of the laws; no target read |
| H4′ | `room 38,2 42,6` | floor at nine cells: 39 to 41 of rows 3, 4 and 5. No cell becomes rock | passed through a check of the laws; no target read |
| H5 | `paint floor 60,70,90` | the class floor is 60,70,90 throughout; no cell changes | run in another design |
| H6 | `open 40,29` · `close 40,29` | the parent itself; and so the compiler refuses, `COMPILE-EMPTY` | a design like it was run |

H4, as he saw it in the court, the parent on the left and the target on the right (columns 19 to 27, rows 23 to
29):

```
  #########     #########
  ##.....##     #########
  ##.....##     ##.....##
  .........     .#.....#.
  ##.....##     ##.....##
  .........     .#######.
  #########     #########
```

**The four laws.** Each is a theorem of the reading, ratified as a property of the language, with its condition.

| the law | its condition |
|---|---|
| corner order | for `open`, `close` and `room`, a rectangle given by two opposite corners in any of the four ways denotes the same map |
| fixed point | a design that is not refused on a parent and has the target T is not refused by a guard on T and has the target T. Its change set there is empty, so the compiler's answer there is `COMPILE-EMPTY`. *The denotation is unchanged*; recompiling is not an accepted no-op |
| room | `room A B`, and `close A B` followed by `open` of the rectangle one cell inside, denote the same map: the same target on every parent, and a guard refuses one exactly when it refuses the other |
| exchange | two adjacent statements whose maps agree on every target both name may be exchanged. Whether the design is refused does not change; the line named may. No law is claimed where they disagree: there the later wins |

His conditions on these are kept: ratified only as *owner-ratified properties of the language*, and no *blanket
commutativity law*. The instances the rows will run are named in the entry, and were checked on the reference
before it was committed. All held, and a pair that disagrees on its overlap did not commute.

**The plants, and what the registration found about them.** Five, by his list, each planted alike in the compiler
and in the reference so that their bytes agree: a room whose rim keeps its openings; a first statement that wins;
corners taken in one order only; an entrance that writes nothing; a paint of a class's own colour, or a net-zero
design, written as operations. The draft said at least one would be caught by this court alone. Read against
DESIGN-IR/DIFF-0 before the entry was committed, that could not be promised: that rung registered the values of one
design, computed before any plant, and outcomes in words, and each of the five appears to change something
registered there. So the entry does not claim a catch no other row makes. The build records which rows of either
rung catch which plant. What this court adds is adjudication, and targets that are the owner's and not a program's.

**The independence fence, and how far it holds.** His: semantic targets are fixed without consulting the compiler or
its reference's output. The targets are data in the entry, and at the build the gate makes each target's bytes
from those cells and the parent's bytes, calling neither program. How far it holds is in the corpus table's last
column: the court was not blind to the reference in four of the ten designs.

**What it does not establish (his list).** Compiler correctness. VRDNP2 correctness. Admission correctness. Authority
legality. Designer intent. Completeness of the language.

**Semiotics is not in it.** Declared, a vocabulary audit. The court leaves it three notes: `entrance` promises a
relation its write does not check; `room` is a statement and not an object; `paint` replaces and does not tint.

**The outside reading behind the recommendation, attributed and not claimed.** Opened on 2026-10-07. The lens laws
of bidirectional programming, for writes that compose (GetPut: putting back what was read changes nothing; PutPut:
the later put wins). SQL's immediate and deferred constraints, as PostgreSQL documents them, for the two levels of
Case 1. Patch theory, as Pijul's manual states it, for when changes commute. RFC 9413, on what tolerating
unexpected input does to a protocol, for refusing where a guess was possible. A dungeon generator's connectors
(Nystrom, *Rooms and Mazes*), where a door is a tile that satisfies a relation, for keeping that relation out of
`entrance`. Git's refusal of an empty commit, for Case 6. Nothing in the entry rests on them.

**The four rows, as registered.** After DESIGN-IR/DIFF-0's five: 247 rows become 251.

| row | what it must find |
|---|---|
| `hermeneutics-preregistered` | the entry at its hash, the ten designs, their literal targets and the laws' instances |
| `hermeneutics-corpus` | the compiler and the reference each give the registered outcome for each design: a batch that, admitted, reaches the content of the literal target; or the code and line. The five plants are run here and in the next row |
| `hermeneutics-laws` | each law on its named instances, for both programs; and the pair that disagrees gives two targets |
| `hermeneutics-fence` | the corpus in the gate is the entry's, value for value; the function that builds a target calls neither program; the rows before keep their names and order |

**When.** By his order: after DESIGN-IR/DIFF-0 is built, its court run and its gate FULL×2. It is not a dependency
of that build.

**Grade.** DECLARED: the court's rulings, the reading, the laws and the registration. OBSERVED (the build
container, before the entry): the laws on the reference, and the reference's outcomes for the designs the table
marks. MEASURED (host): the gate with the registration applied, 242 of 242, one run; pushed
(`5c8ad19..11afebf`, carrying 0142 to 0144). Nothing is ESTABLISHED: nothing of it is built.

**does_not_show.** That the reading is what a designer means. That either program implements it. That the language
is complete. That the court was independent of the reference's author: five of six rulings are a ratified
recommendation.

**Falsifier (of the registration).** A literal target that the parent's cells and the ruling do not give. A law
whose condition admits a counter-example under the reading. A row that takes a target from a program.

## The open clause, now with named rungs (skybox, physics, the proposal machine)

New semantics the studio did not inherit from Urðr, recorded so they are built on purpose and not by accident:

- **SKYBOX-0 (new VIEW semantics).** The sky is `vista`'s LUT sky-bands per depth, frozen in Urðr. Authoring a
  skybox is a VIEW law Urðr never certified, so it takes one of the two open-clause routes: earned in Urðr and
  re-frozen under a new oracle tag (the route the bearing camera took to `urdr-oracle-2`), or a Verðandi-local VIEW
  reference pinned by rows here. Not built until a
  route is chosen and a semantics exists to render it.
- **PHYSICS-0 (CORE semantics — corrected).** An earlier version of this clause said the frozen oracle holds no
  physics. That was wrong, and the correction is checked against the tag. `urdr-oracle-1` carries Urðr's
  `tools/physics`: exact mechanics over ℤ/ℚ (rungs 1–4: 1D and n-D dynamics, the frictionless n-contact LCP,
  articulated joints), the bounded Q32.32 fixed-point path (rung 5), and scalar-field transport with its coupling to
  bodies, all with frozen conformance corpora, and std-only Rust cross-placements of rungs 1–5. It also carries
  `tools/netcode`: a lockstep spine, rollback, authored worlds in the tick, and regional authority. These are CORE
  semantics already earned in Urðr and frozen at the tag this repository cites, so they can reach Verðandi by the
  GAME-0 route (verbatim import, manifest, the tag's own suites run in place) with no re-freeze and no second
  authority. None of it is imported yet; GAME-0 carries only the two modules `kinema` needs. What the tag does *not*
  carry is still new CORE semantics with one route only, earned in Urðr and re-frozen: Urðr's own `contact` law
  records that its 3D tick does not exist yet. The studio authors no physics that a certified semantics does not
  already define.

- **LLM-BUILDER-0 (a proposer outside authority — declared, the owner's goal of 2026-10-02).** The model may propose
  becoming; only the verifier may admit it. A model would emit typed proposals anchored to a session head and an
  authority digest. The verifier refuses or admits; an admitted proposal is a session event like any other, its
  consequence shown by the reference, and the model's text is provenance beside the event, never authority. A stale
  anchor is rebased explicitly or refused. Nothing is built and no model is in the tree. It is not seated; when it is,
  it registers its own hypothesis and failure condition. Until then it constrains the rungs before it: every event
  kind typed and replayable without its source, provenance never folded into the head, no path that executes text.
  The design is in [`docs/ROADMAP.md`](../docs/ROADMAP.md).
- **Program time and content time; the design-event stream (declared with LLM-BUILDER-0, the owner's, 2026-10-03;
  by his ruling of the same day, what the route builds towards).**
  The engineering gate certifies the program and runs when the program changes. Content is admitted by a check on the
  artifact itself and does not invoke the gate; a model may generate content and may not redefine the laws content
  runs under. Conversation is meant to become the editor: intent becomes a bounded world diff, previewed on a
  speculative branch, and what the verifier admits is a design event in the session. Language can propose, the
  verifier admits, the session records, the kernel renders. Nothing is built. Today the only content is a session's
  events over W and M, admitted by seal, base, fold and replay, and the world has no regions, heights, structures or
  named objects for a design vocabulary to refer to. Four rules already in force meet it and want rulings before any
  rung: commit-only (a preview only as a speculative worldline, never shell state), earn the authority (new world
  semantics come from Urðr), the witnesses a lighter check must still ask for, and merges as explicit anchored
  events. Recorded in [`docs/ROADMAP.md`](../docs/ROADMAP.md).
- **ADMIT-0 (the admission seam — chosen in the owner's court of 2026-10-03; registered and built, its own section
  above; the gate passes on the host and the first admission is sealed there).** The
  first rung towards the design-event stream. Windowless: a typed, anchored proposal read from a file is refused or
  admitted, and an admitted one is an ordinary session event in today's vocabulary (a cell edit, a tile edit) with
  its envelope beside it. A stale anchor is refused, always, naming both heads; rebase is a later rung. No model is
  in the tree and no gate runs at content time. The owner then asked for a search for hardenings and reviewed what
  it found. His review's rulings: one strict recognizer for a proposal language smaller than JSON, with every other
  component receiving the typed proposal and never the text; an anchor that binds the program, the renderer, the
  head and the proposal's schema; a proposal id apart from the digest of its bytes; typed refusals; a scope the
  verifier enforces; provenance on the result; and seven courts registered with the rung and not before it (reader,
  single parser, anchor, capability, idempotency, crash, replay). In his words: *the gate certifies the machine;
  ADMIT admits the world's changes.* OBSERVED while checking the research, outside the gate: the saved-form reader
  compiled alone and Python's `json.loads` differ on 12 of 19 hostile inputs, and the Rust reader panics on two and
  aborts on one. That does not show any sealed record wrong; the reader was not run through the shell, and no row
  holds it. A second court then ruled for the registration: the proposal language is a line language whose
  accepted bytes are the canonical form (`VRDNP1`, frozen; a later language is a new version), its digest the
  SHA-256 of the exact bytes; the saved-form reader is hardened in its own rung after this one (`READER-COURT-0`),
  its files re-pinned once there; the admitter grants the scope; the anchor is what a session already records
  (renderer identity, bearing identity, head, language version), and no program identity is minted. The owner's
  order: ADMIT-0, `READER-COURT-0`, `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0`, then branch and preview. A third court
  fixed the lines (eight; no program line, no scope line) and the proposal id (the proposer's 64-hex handle).
  **Registered** (`bdd38593`) as its own commit: the bytes of `VRDNP1` (327 to 337 bytes, one byte sequence per
  typed proposal, a worked example and its digest), the anchor, the grant, the envelope beside the event and never
  in the head, typed refusals in a fixed order, and the rows `admit-preregistered`, `admit-reader`, `admit-single`,
  `admit-anchor`, `admit-capability`, `admit-idempotent`, `admit-crash`, `admit-replay` and `admit-fence`.
  MEASURED on the owner's host: the gate passes with the entry in the registry, 209 rows, rowset
  `a15345720a81009c`, pushed as `0669ecf`. Those rows are the gate as it stood plus the registration; none of the
  entry's success conditions is shown yet. The owner accepted the registration as the design, with its limit kept
  explicit: the admitting shell records the digest of the bytes it received, and no later verifier can recompute it,
  because the proposal's bytes are not kept. In his words the state is `REGISTERED / BUILD PENDING`. The courts, the
  research with its sources, the table, the review, the registration and the acceptance are in
  [`docs/ROADMAP.md`](../docs/ROADMAP.md).
- **The design language: one design authority, many editors (declared, the owner's, 2026-10-03; not registered,
  nothing built).** The design environment as a typed, deterministic, inspectable program: design objects,
  relations and constraints and not tools; constraints as persistent objects with witnesses; one authority seen
  through many projections (spatial, gameplay, simulation, narrative, performance); a model given a design language
  and nothing else. *Don't build an AI level editor. Build a deterministic design language with many editors.* It
  proposes a small rung, `DESIGN-IR-0`, which is a declared name and not seated: where it sits against the owner's
  locked order was not ruled. Nothing in the tree is a design object, a relation or a constraint, and the world has
  no units beyond cells. It meets rules in force: anything that decides W or M is earned in Urðr; a constraint's
  status is a witness to recompute and not a field to trust; integers of the world and no floats; a panel and no
  score; preview only as a speculative worldline. Recorded in [`docs/ROADMAP.md`](../docs/ROADMAP.md).
- **READER-COURT-0 (the saved form's readers brought to one verdict — chosen in the owner's courts of 2026-10-04;
  registered `f53017cd` and built, in its own section above).** The rung after ADMIT-0. Read from the code
  first: four Rust JSON parsers (one
  text in three files, and a different one in `workshop/edit.rs`), four Python readers using `json.load`, three
  writers with three layouts, and a corpus that sits inside a small language (no fraction or exponent in any of 39
  record files; depth 7 at most — this line first said 6, corrected in the section above). The rulings: the accepted language is the bounded language the tree's registered
  writers are permitted to emit, its bounds derived from the writers and not from the files; one Rust reader in
  one file shared by path, owning parsing and nothing else; an independent strict Python reader, with no
  `json.loads` underneath, held against it by the court; the same code and the same byte offset on every hostile
  file; every reader of the saved form covered; one escape spelling, the workshop's writer aligned; signed 64-bit
  the format's law, writers refusing beyond it; exhaustive single-byte mutation on small registered documents and
  boundary mutations on real files. In the owner's words: *corpus establishes coverage; the writer contract
  establishes the language.* Recorded in [`docs/ROADMAP.md`](../docs/ROADMAP.md).
- **Hermeneutics and semiotics (two texts the owner brought, 2026-10-07; hermeneutics since registered as
  `HERMENEUTICS-0`, `22d52d02`, in its own section above; semiotics declared; nothing built).**
  DESIGN-IR/DIFF-0's amendment says that a misreading of a statement shared by the compiler and the reference is
  caught by neither of its equalities. The owner named the layer that gap belongs to. `HERMENEUTICS-0`: *What is
  the authoritative meaning of VERDANDI-DESIGN 0, independently of either compiler?*, defined as *a registered
  adjudication of the denotation of the source language* and not as what a designer probably meant, held by a
  semantic corpus of the owner's own rulings, each LOCK, DEFER or REJECT, and never by a panel or a model. His
  ruling: *LOCK: introduce the concept now. DEFER: its implementation/build until after DIFF-0. REJECT: folding it
  into DIFF-0 or treating compiler/reference agreement as hermeneutic evidence.* Semiotics, in his second text, is
  one level earlier, what a sign stands for, and is a vocabulary audit and not a rung. Both are declared names and
  are not seated. Recorded in [`docs/ROADMAP.md`](../docs/ROADMAP.md).
- **The development environment: fifteen pivots (declared, the owner's, 2026-10-04; not registered, nothing
  built).** A review of Verðandi as a research-grade interactive development environment: a design space as a
  window, docking, view modes, constraints as a visible subsystem, a design diff, a parameter rack, recipes, a
  preview unmistakably not the world, a command palette, portable project bundles, a compatibility inspector,
  capabilities, a plugin SDK around projections, multi-representation editing, and a design observatory. *The
  visual editor does not become the source of truth.* Its order puts READER-COURT-0 first, then a design
  representation, the design diff and constraint objects; how that stands against the owner's locked order was not
  ruled. It meets rules in force: no floats, units or scores; a constraint's status a witness; shown numbers are
  measurements; preview only as a speculative worldline; a batch a new language version; a plugin inside the
  program is code the gate did not certify. Recorded in [`docs/ROADMAP.md`](../docs/ROADMAP.md).
- **REASON-COURT-0 (preregistered `337ab021`; nothing built).** Its census is taken, its courts are held and its
  register is in the tree. See its own section above, and [`docs/ROADMAP.md`](../docs/ROADMAP.md).
- **Self-optimizing code, and its correction to a layout court (declared: two texts the owner brought, 2026-10-04;
  considered at his word; not registered, nothing built).** The first text proposes a toolchain that mutates the
  kernel's memory layout, thread partitioning and instruction selection continuously, on live workloads, with byte
  identity as the kill switch and automatic adoption of whatever is faster, and calls the result invisible to
  memory-scraping cheats. The owner: *i think you should pause for this tool for this repo*, and in court,
  *consider:*. Considered, one thing fits (LOCALITY-0's court, mechanized over a registered finite space) and seven
  collide: live measurement against the theorem it cites; a self-changing program the gate did not certify and no
  renderer identity names; automatic adoption against `built ≠ adopted` and the drift on record (G10, G13); byte
  identity over a court set as evidence about that set only; run-time code generation against std-only; the ruling
  of 2026-10-01 that the staircase reopens only when a court misses its target; and a security claim with no
  threat model under it. The second text accepts this and offers a static, compile-time layout court it names
  `SYNTH-LAYOUT-0`, a declared name and not seated. It still meets rules in force: the gate times nothing, a build
  does not choose the renderer, an adoption needs a margin and a confirming run, the court set is this tree's and
  not Urðr's twenty witnesses, and three of its terms (`conventions.py`, an Arbitrary-Boundary Law, Temporal
  Fidelity Accounting) are not in this tree. Lawful is not next: the order is unchanged and READER-COURT-0's build
  is next. Recorded in [`docs/ROADMAP.md`](../docs/ROADMAP.md). *On the host:* this record was applied (0112), the
  gate passed with it (218 rows, rowset `0b423b279a40c85c`, 0 fail, 0 skipped) and it was pushed,
  `25b5c17..b847810`. The owner's word after it: *take the next.*

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
  off-gate) — naming the memory/locality axis as a candidate and committing no optimization; its RE-BREAKDOWN-1b
  refinement (constant-anchor probe) confirmed the tile fetch leads the map indirection ~4.4× on the host once the
  anchor tax was cancelled. LOCALITY-0 (seated) opened the data-layout court on that finding — the floor tile re-laid
  out as an 8×8 cache-blocked or Morton Z-order execution FORMAT, both proven byte-identical, both a lossless bijection,
  content-provenance held apart from format — timed process-isolated under the Epistemic-Invariance boundary
  (`verify/locality0.py`), with three exits (blocked / morton / neither → capacity stall → GAUNTLET-2). The host court
  fired **Exit 1**: blocked won byte-identical and faster (8185→7734 µs p99, ~1.07×, the lower index tax of the two),
  and the **LOCALITY-0 LOCK** (seated) promoted `emit_swizzled<BLOCKED>` to the accepted single-thread `fast::emit` —
  monomorphized, the floor swizzled once at scene load, the linear-fetch DDA retained verbatim as the `emit_linear`
  reference witness. **GAUNTLET-2+** (multi-threaded column stripping) inherits the LOCKED blocked emit's sealed 7734 µs
  p99 as its hard baseline, to be beaten under partition invariance — the certified picture byte-invariant under any
  column partition and thread count, adversarial partitions included (preregistered `711cc1d4`, decision rule and all).
  Both GAUNTLET-2 courts then landed: the **correctness court** (seat 20) proved `emit_partitioned` byte-identical over
  contiguous + adversarial partitions, and the **performance court** (seat 21) added the execution-only `emit_threaded`
  (`std::thread::scope`, one contiguous group per thread) with byte-identity gate-enforced at every `T` and the
  `T | correctness | p99` matrix vs the inherited 7734 µs sealed off-gate by `verify/gauntlet2.py`. The host court fired
  **PROMOTE** (every `T>1` beat 7734, reproduced on a second sweep; T=16 fastest ~3.35–3.50×, T=8 the stable knee ~3.3×),
  and the **GAUNTLET-2 LOCK** (seat 22) adopted the threaded emit as the production render (`fast::render` at the default
  `PROD_THREADS = 8`), rewiring the shell to render through it. Whether that headroom reaches composited output is a
  measurement, not an inference: **LATENCY-1** reruns the fixed session through LATENCY-0's unchanged instrument —
  which, as the amendment **LATENCY-1a** records, times only blit → composited over frames rendered before the window
  opens, so it cannot see the renderer — and **LATENCY-1R** puts the render inside the clock (render-start →
  composited, T=8 vs the single-thread reference, locked and uniform phase), preregistered before its number.
- **PRESENT-1 (flip-model / waitable-swapchain).** LATENCY-0 *established* only that the composed-GDI present is
  refresh-coupled. PRESENT-1's *hypothesis* — falsifiable, to be measured, never assumed — is that a flip-model
  present CAN decouple present latency from refresh; it becomes experimentally valuable once the render fits the
  budget (so it is not competing with an 11.6 ms render). Off-gate/host; HARDWARE-144 additionally needs a ≥144Hz panel.
- **Interactive capture (parallel, not entangled with the performance chain).** The inverse of SHELL-PLAYBACK:
  raw window/device event → binding → typed action/edit → SESSION-WALK append → the SAME sealed representation
  headless authoring produces. A shell/input problem, not a new authority; measured against the existing session
  machinery, never modifying it. *Since built, under other names: LIVE-INPUT-0, LIVE-SESSION-0, LIVE-AUTHOR-0 and
  MOUSE-LOOK-0, each in its own section above.*
- **The named future slices** (courted, not seated): IMPOSSIBILITY-0 (measured negative results as level
  preconditions), SEMANTIC-0 (a float-free, geometry-bound semantic layer as a Verðandi-local new-semantics
  authority), MERGE-0 (deterministic commutative merge of non-conflicting edits, stripped of consensus/time).

The boundary holds end to end: SESSION-WALK proves what is becoming, SHELL-PLAYBACK proves the window shows
exactly that becoming, LATENCY-0/GAUNTLET measure how fast it is produced and shown — and every performance step
survives the same pixel-level oracle, so speed is never traded for correctness and a failed experiment stays
permanently useful evidence. The skybox stays beyond the frozen oracle, gated behind the new-semantics route;
physics is in the tag, and reaches the studio only as imported evidence by the GAME-0 route (PHYSICS-0 above).
