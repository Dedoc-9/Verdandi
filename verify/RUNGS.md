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
screen line. The presenter decides and counts a mismatch before it names one, and names it only on the lines it
prints. The court's hook is a trait method whose default names nothing, so a surface without it keeps its old message.

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

**Grade.** DECLARED: the method. ESTABLISHED (gate): the one-to-one invariant on the court, append-only growth, the
default path, the unchanged refusal under a failed append, the reader. ESTABLISHED (source): the presenter's call sites.
NOT_MEASURED (host): no host refusal has been logged yet.

**does_not_show.** Why a refusal happened: a count is not a cause. That a refusal cannot occur: zero records is not
proof. Refusals outside the admitted operations: argument errors, the windowless build, and the host window court's
harness (the shared DWM prelude and the window's creation, before the court function starts). The presenter's records
executed on the gate: `show` needs a window, so its call sites are fenced from the source. A record whose append failed
(the console says so). Timing: `unix_ms` is the wall clock, for grouping only.

**Falsifier.** `refusallog-bijection` goes red if a refusal prints without a record, leaves two, or leaves one that does
not match its printed code and registered attribution; if the log is rewritten; or if a failed append changes the
refusal. `refusallog-fence` goes red if a presenter refusal bypasses the primitive, the court writes or prints its
own refusal, the writer can truncate, anything else names the log, or the gate stops isolating its own refusals.

## The open clause, now with named rungs (skybox, physics)

New semantics the studio did not inherit from Urðr, recorded so they are built on purpose and not by accident:

- **SKYBOX-0 (new VIEW semantics).** The sky is `vista`'s LUT sky-bands per depth, frozen in Urðr. Authoring a
  skybox is a VIEW law Urðr never certified, so it takes one of the two open-clause routes: earned in Urðr and
  re-frozen here as `urdr-oracle-2`, or a Verðandi-local VIEW reference pinned by rows here. Not built until a
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
  machinery, never modifying it.
- **The named future slices** (courted, not seated): IMPOSSIBILITY-0 (measured negative results as level
  preconditions), SEMANTIC-0 (a float-free, geometry-bound semantic layer as a Verðandi-local new-semantics
  authority), MERGE-0 (deterministic commutative merge of non-conflicting edits, stripped of consensus/time).

The boundary holds end to end: SESSION-WALK proves what is becoming, SHELL-PLAYBACK proves the window shows
exactly that becoming, LATENCY-0/GAUNTLET measure how fast it is produced and shown — and every performance step
survives the same pixel-level oracle, so speed is never traded for correctness and a failed experiment stays
permanently useful evidence. The skybox stays beyond the frozen oracle, gated behind the new-semantics route;
physics is in the tag, and reaches the studio only as imported evidence by the GAME-0 route (PHYSICS-0 above).
