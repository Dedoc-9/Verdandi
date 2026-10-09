<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Roadmap — toward a live, authorable world

*Where the program stands, what "a live authorable world" means for it, and the sequenced, falsifiable path to get
there. This roadmap names rungs that are already public in [`verify/RUNGS.md`](../verify/RUNGS.md), and — since the
owner published it — the route to walking in a live, authorable world, whose rungs are named but not yet built. The
general techniques it points at are cited prior art, not commitments. Other candidate rungs are under private
consideration pending the owner's consensus and are not enumerated here.*

---

## Where we are

Two halves of the studio are built and sealed. The **render** half is fast and honest: the emit is ~3.3× faster than
the certified baseline (a stable ~2,355 µs p99 at eight threads), byte-identical to the frozen oracle at every step,
and the shell now renders through that parallel fast path. The **authoring** half already exists in skeleton:
`WORKSHOP-0/1` turn an edit into a new authority with a hash-chained consequence record; `INPUT-0` turns shell input
into a typed command and a new camera that replays headless; `SESSION-WALK` interleaves moving and authoring into one
sealed chain; and `SHELL-PLAYBACK` proves the window shows *exactly* that sealed becoming. And since `GAME-0`, Urðr's
**game layer** — seventeen discrete vertical slices, from level generation through the input membrane, with their
corpora and suites — sits in `oracle/game/` as frozen evidence from the same tag, passing its own 411 tests in place.

The loop between the two halves is now joined (this paragraph read otherwise until 2026-10-04, and the route below
is how it was closed). The **live editor** renders every composition from a session being written as it runs: a key
or a mouse report becomes a typed event, the event is journaled, the world is the log's replay, and the session is
saved, verified and resumable (`LIVE-LOOP-0` through `MOUSE-LOOK-0a`, each measured on the owner's host). The camera
turns to any registered heading, on a renderer held byte for byte to a reference carried from `urdr-oracle-2`. And
the first **admission** seam is built and measured: `ADMIT-0` recognizes a proposal in a line language or refuses
it, and admits it as one ordinary edit.

And everything the tree saves and reads back is now one bounded language with one verdict from every reader
(`READER-COURT-0`, built; the gate passes on the host, 226 rows, and is pushed).

And every refusal the gate requires is now held to a registered reason (`REASON-COURT-0`, `337ab021`, built: six
rows), and every refusal raised inside the gate's own process is claimed by a row, a class, a site and a count
(`MINT-WATCH-0`, `cd1472ec`, built: four rows). The gate was then 236 rows.

With that the owner ruled the engineering seam frozen (2026-10-06): no further gate unless a real invariant is
found, and the work is the design environment. Its first piece is built off the gate: `design/`, five verbs over
the certified admission seam.

One invariant was found there, by measuring, and it is built: a design is admitted as one batch or refused whole
(`DESIGN-EVENT-0`, `ae7cbb36`, built: six rows). With it the gate was 242 rows and passed here and on the host. By the
owner's word with that push no theorem was added at once. When the host's gate was FULL×2 by his own predicate, his
word was *take next* (2026-10-07).

That next rung is built: the step from a design to its change set, which was the one uncertified link between the
design tool and the admission (`DESIGN-IR/DIFF-0`, `2baa42f3`, five rows). The gate is 247 rows and passes here and on
the host, FULL×2 there by the owner's predicate, and is pushed. Registered behind it, and now free to be built at his
word: the meaning of the design language as the owner's own rulings, literal targets and laws, which neither
program computes (`HERMENEUTICS-0`, `22d52d02`).

What is *not* yet done: that compiler; design objects that outlive admission, constraints, and a model at the seam
(declared, not registered); any measurement of the live loop's timing; richer edits than a cell and a tile class;
and semantics the frozen oracle never certified.

---

## What "live authorable world" means here

Not a general game engine. Specifically: **a running window in which an author changes the world, the change becomes
a new authority through the sealed workshop path, the projection updates live, and every frame on the screen is
provably the consequence of that authored history** — with new kinds of world content (skybox, filtering semantics,
physics beyond what the tag carries) admitted only when they *earn* an authority, either carried or re-frozen from Urðr
or pinned by a Verðandi-local reference. The bar is the one the program already holds itself to: `built ≠ adopted`, `declared ≠ verified`, and no
semantics reaches the screen without passing through a gate.

---

## The gap, in four questions

1. **Does the render headroom reach the screen?** Measured twice (`LATENCY-1R`): yes for work arriving at a random
   phase (composited output 3.2–3.6 ms earlier at the median), no for a loop that renders right after it presents
   (under 1% gets through the refresh-coupled GDI present). The shell's whole render-start → frame-ready interval is
   14.8–15.7 ms at p50, longer than one refresh on the owner's host, and FRAME-SPLIT-0 found, twice, no single phase
   dominating it (blit largest at 427–434‰). Renderer latency: materially improved. End-to-end presentation latency:
   phase-dependent, no low-latency or competitive claim. The largest phase, the blit, is mostly the 2:1 reduction here:
   at 1:1 it drops ~5.3–5.6 ms (PRESENT-SCALE-0, confirmed on this host). At half size, `COLORONCOLOR`'s blit was
   materially cheaper than the default `BLACKONWHITE`'s in both runs (392‰ and 449‰; `HALFTONE`'s reading did not
   reproduce) (PRESENT-STRETCH-0). Reusing the frame's buffers instead of allocating them every frame took 1.6–1.8 ms
   off the envelope (ALLOC-REUSE-0, confirmed). In this loop most of each saving waits at the composition instead. *(G7 — measured; G8 —
   confirmed, NO SEAT; G11 — confirmed.)*
2. **Can an author edit the live window?** Yes, since the live rungs: keys walk and edit, a mouse turns the
   camera, tile classes are painted, and each is a typed event in one saved, verified session (`LIVE-INPUT-0`,
   `LIVE-SESSION-0`, `LIVE-AUTHOR-0`, `MOUSE-LOOK-0`, each measured on the host). The vocabulary is small on
   purpose: a cell opened or closed, a tile class painted. What it costs in time is not measured.
3. **Can the world hold semantics the oracle never certified?** The skybox and filtered VIEW semantics live *beyond*
   the frozen oracle and need the new-semantics route. Physics is different: much of it is already in the tag (see
   below), so the question there is what to carry, not what to invent.
4. **Can independent edits combine?** Two authored branches of a world need a deterministic, consensus-free merge.

---

## The route to walking in a live, authorable world (the owner's order)

The substrate is built: a deterministic world, deterministic materials, a deterministic renderer, an exact presenter,
workshop authority and the session walk. What is missing is the **closed live cycle**: input → authoring authority →
render → present → observe → next input. It is mostly not a renderer problem any more. It is the live loop, live
input and authoring, and making the live chain recoverable. The order:

```text
REFUSAL-LOG-0 → RUN-LEDGER-0 → REFUSAL-WHY / DRIFT-0      the diagnostic foundation (DRIFT-0: sitting 1 of 3 complete)
      ↓
LIVE-LOOP-0      the shipped per-frame loop — walked on the host: 246 compositions live, every readback exact
      ↓
LIVE-INPUT-0     physical input → typed editor action → the workshop/session → a new W, M → the next frame — walked and edited on the host by key presses, every readback exact
      ↓
LIVE-SESSION-0   live events → append-only session → save → restart → replay → the same world — a host walk saved, resumed into a new file, both replayed here
      ↓
LIVE-AUTHOR-0    the thing authored is the same authority the next frame renders — painted live on the host by class keys, saved, resumed there with the painting intact
      ↓
HOLD-WALK-0      held keys walk the grid: the input continuous, the world discrete — measured on the host; not the free movement the owner wants
      ↓
(Urðr)           VIEW-YAW-0: the turning camera earned in Urðr and frozen as urdr-oracle-2 — any heading, the eye still at a cell centre
      ↓
BEARING-0        the bearing camera carried and its reference kernel placed: all 104 witnesses of urdr-oracle-2 bit for bit — built; the gate passes on the host
      ↓
BEARING-FAST-0   the production candidate, held byte for byte to the reference — measured on the host: exact stepping in eight row bands, worst-camera p99 3,716 us (target 6,667); the sweep 622,440 of 622,440 equal
      ↓
SIM-TICK-0       the mouse-look rules as integer law, windowless: the 64 Hz tick, one command per tick, the look event in the one session, reference certification at save — built; the gate passes on the host with the same 197 rows
      ↓
SIM-TICK-0a      two rulings of MOUSE-LOOK-0's court that are rules of the tick, still windowless: a sensitivity change is a typed configuration event in the session, never folded; a held key walks once a tick — built; the gate passes on the host with the same 201 rows
      ↓
MOUSE-LOOK-0     a real mouse on those rules: captured until Esc (shell state, never session state), raw counts into the 64 Hz accumulator, the command into the existing live loop, the picture alone at a free heading, every 64th free-heading frame recomputed off the loop — built; the gate passes on the host; the first window run walked on keys with no mouse report; on the second, under MOUSE-LOOK-0a, a real mouse turned the camera
      ↓
MOUSE-LOOK-0a    an amendment from the owner's review and the first host run: a composition applies at most one closed tick command and span counts tick boundaries between compositions; a run its Esc ended is recorded as escape; the window counts the raw input it receives before it reads it — built; the gate passes on the host with the same 209 rows; the second host run is the execution witness: 13,931 raw reports, 1,761 looks, 1,775 of 1,775 free-heading frames the reference's, a focus loss with no session event
      ↓
the presentation and latency measurement      input to photon in separate segments; frame rate alone is no competitive claim
      ↓
richer edits     vocabulary on the one live editor, not new pathways
      ↓
walking in a live, authorable world
      ⋮
LLM-BUILDER-0    a declared goal beyond the route: a model proposes typed, anchored changes against the sealed session; only the verifier admits them — nothing built, and the route above is built in respect of it. Declared with it (2026-10-03), and by the owner's ruling what the route builds towards: the gate certifies the program and content is admitted, not gated; conversation edits the world through a stream of admitted design events
ADMIT-0          the first rung towards it, chosen in court (2026-10-03) and by the owner's order next after MOUSE-LOOK-0: the admission seam. One strict recognizer for a line language whose accepted bytes are canonical (VRDNP1), an anchor refused when stale, a scope the admitter grants, an admitted proposal an ordinary session event. The gate certifies the machine; ADMIT admits the world's changes — registered (`bdd38593`), built, and measured on the host: the gate passes there and the first admission is sealed
      ↓
READER-COURT-0   next by the owner's order, its courts held (2026-10-04): the saved form is the writers' language and nothing wider; one Rust reader shared by path; an independent Python reader held against it, the same code and byte offset on every hostile file — registered (`f53017cd`) and built: eight rows, 226 in the gate; on the host 225 of 226 on the first run, 226 of 226 with the fix, pushed
      ↓
REASON-COURT-0   the owner's ruling (2026-10-04): next after READER-COURT-0 and before DESIGN-EVENT-0. Every refusal check in the gate is held to an expected reason, an exact code or a deliberately open REFUSE(any). Its census is taken (145 refusal checks in 78 rows; 103 hold a code), its courts are held, and its register is in the tree: codes only from a requirement that already exists, a watch over every child that does not end 0 reading only the code head, the sealers under one registered mutation — registered (`337ab021`) and pushed; in three configurations here and on the host every registered group held — built: six rows, 232 in the gate; on the host 232 of 232, pushed
      ↓
MINT-WATCH-0     the owner's ruling (2026-10-05): a separate slice, registered now and built after REASON-COURT-0's build, before any rung that gives a refusal a code or makes it a datum. Every refusal-class raise inside the gate's own process is attributable to a registered row, class, site and count, or is a registered plant of the gate. Sites from source (164 in 15 files), counts measured (142,082 mints, four configurations agreeing); a site is its file, its function and the text of its raise — registered (`cd1472ec`) and pushed — built: four rows, 236 in the gate; on the host 236 of 236
      ↓
the adjustment   the owner's ruling (2026-10-06): the engineering seam is frozen; a new gate only for a new engineering invariant; the work is the design environment. Built off the gate, content time: design/ — inspect, propose, preview, admit, undo over the certified seam, driven the same way by a person, a script or a model
      ↓
DESIGN-EVENT-0   locked as the next rung by the owner (2026-10-06), seven properties in one court: a canonical batch of one to 4,096 typed operations is refused whole or admitted by one admission as that many ordinary edits, equal to the same operations admitted one at a time. N edits and one admission; VRDNP2, a net change set with one byte form; full replay with an exact memo; a dry run bound to its admission — registered (`ae7cbb36`), pushed, and built: six rows, 242 in the gate; the 60 operations admitted one at a time before the seam existed reach the same head as one batch; on the host 242 of 242 on every run and FULL×2 by the owner's predicate; pushed
      ↓
DESIGN-IR/DIFF-0 the owner's word *take next* (2026-10-07), given when the host's gate was FULL×2 on DESIGN-EVENT-0; his court the same day, four answers locked: the compiler first, in the certified shell with an independent reference in the gate, the proposal id the SHA-256 of the exact design bytes, readings and constraints out by name. The current design text is the source language, and its compile to the canonical VRDNP2 change set against a parent world is one tree-owned function — registered (`2baa42f3`); read and locked by him the same day, and the round around it named before the build as subcourts and no new claim (`DESIGN-IR/DIFF-0a`, `c414587d`); both pushed (`83b0261..5c8ad19`); built (2026-10-07): the compiler in the shell, five rows, 247 in the gate, every registered value reproduced; two rows of DESIGN-EVENT-0 changed in their text by his ruling, the amendment chain named a law and its origin registered (`REASON-COURT-0b`, `d51b4d20`; `DESIGN-IR/DIFF-0b`, `42ac51f5`); the design tool a client of the compiler; on the host 247 of 247 twice on one tree, FULL×2 by his predicate, pushed (`11afebf..c8b6a1f`); his rulings of 2026-10-08 registered and built into two existing rows (`DESIGN-IR/DIFF-0c`, `38b51bed`): the layout relation and the origin as a projection
      ↓
INPUT-0a         the owner's ruling (2026-10-08): the small semantic fix first, before the next rung. G31 repaired — a walk's path is the rest of its line, one existing row carries a space, the pin moved by the chain's third link (`REASON-COURT-0c`, `94f3de68`) — registered (`2f0426d6`) and built, 247 rows; the perturbed pass that found it, run again as predicted, 247 / 0; the host's clone with a space, 247 / 0 twice, FULL×2; pushed (`59edc01..a16d663`). G33 investigated after it: the contract the owner's to rule
      ↓
INPUT-0b         G33 for the walk's rung (2026-10-09), by the owner's instruction to find the most elegant path and carry it through: the rows ask for the kernel and the walk program where they use them (Lazy Setup; a brittle's fix, after iFixFlakies), held by `input-demo` — registered (`a167c308`) and built, 247 rows; each walk row passes run alone; FULL×2 on the host by the witness, pushed (`89d082e..b386b85`); CLOSED by his ruling (2026-10-09), the witness's read order deferred
      ↓
HERMENEUTICS-0   named by the owner (2026-10-07) for the gap DESIGN-IR/DIFF-0's own amendment states: the meaning of the design language, apart from either program that compiles it. The concept locked, its build deferred until after DIFF-0, folding it into DIFF-0 rejected. Semiotics, one level earlier, is a vocabulary audit and not a rung, declared. His court the same day: one reading ratified, six cases locked, four laws ratified as theorems, a corpus of ten designs with literal targets — registered (`22d52d02`) and pushed (`5c8ad19..11afebf`); not built; built after DIFF-0 is built, courted and FULL×2; PROCEED, his word (2026-10-09); read for the build, two rules of DESIGN-IR/DIFF-0's rows stand in the way of its registered instrument, put to him
      ↓
EVIDENCE-LINK-0  accepted by the owner (2026-10-09) as the next qualifying slice: each claim a commit message or a document copies about a recorded event — ids, push ranges, row counts, hashes, prediction outcomes — traced to its authoritative source, never only to another copy; an instrument outside the repository that reads and reports; declared, defined and registered after HERMENEUTICS-0 is advanced and not bundled into it
      ↓
LIVE-AI-EDIT-0 → GUI      the owner's order after it (2026-10-06); none registered. Design objects that outlive admission, and constraints, are each a court of their own and are not seated. A competitive arena — a map that matches are played on — is declared (a text he brought, 2026-10-08): it gives those two courts their content, and is not placed in the order. Environmental independence, a court that would hold a row's verdict against what its surroundings were not declared to change, is accepted as a future audit mechanism and deferred (his ruling, 2026-10-08). PERSPECTIVE-0, observation stratified from action, reconstruction and claim, is declared (three texts he brought, the same day). REFLEX, a ladder of nine declared steps from perspective types to a reflexive certificate, gathers both (two texts, the same day). None is placed in the order
      ↓
PRESENT-1 (its screen witness settled first), the live-loop re-breakdown, BANDWIDTH-0 / POOL-0; DRIFT-0 continues alongside
```

The owner swapped LIVE-SESSION-0 ahead of LIVE-AUTHOR-0 after LIVE-INPUT-0's host runs. The live loop worked, but its
evidence was still console text that had to be replayed by hand. Durability first means every later host walk,
including LIVE-AUTHOR-0's, is a saved file the workshop verifies, not a transcript.

After LIVE-AUTHOR-0 the owner stops adding bespoke input cases. LIVE-AUTHOR-0 is the last authoring-primitive slice.
From then on the rule is general: every accepted live edit is a typed SESSION-WALK event, the event changes the
authoritative W or M, the next frame is derived from the resulting authority, and the event is durable through
LIVE-SESSION-0. Free continuous movement and richer edits are vocabulary and navigation semantics added to the one live
editor (`shell live-window`), gated in its binding table, not new pathways or rungs. HOLD-WALK-0, registered under its
own name but on the same pathway, made held keys keep walking cell by cell over the same discrete world, because the
frozen renderer draws the eye only at a cell centre facing N, E, S or W. After walking it on his host, the owner judged
that this is not the free movement he wants, and ruled what it becomes: shooter-style mouse-look, taken in rungs. The
turning camera was earned in Urðr first (VIEW-YAW-0, frozen as `urdr-oracle-2`), because no frozen oracle existed to
hold a renderer to outside the four cardinals; here it is carried and placed as a reference (BEARING-0), made fast
against that reference (BEARING-FAST-0), given its rules with no window in the proof (SIM-TICK-0), and only then driven
by a real mouse (MOUSE-LOOK-0). The owner ruled those two are never combined.
Cursor authoring, preview sliders, gizmos and an editor-pane interaction model are deliberately not on the route yet:
those are where a shell starts accumulating an alternate authority.

- **The diagnostic foundation** is not on the critical path to walking. It gives the live loop an instrumented refusal
  surface instead of console archaeology. REFUSAL-LOG-0, RUN-LEDGER-0 and REFUSAL-WHY-1 have landed. REFUSAL-WHY-1
  writes the covering windows into the refusal log as program, class, rectangle and overlay flags. Titles stay
  console-only and are never persisted, and the rectangle is diagnostic geometry, not identity. DRIFT-0 (preregistered)
  repeats the locked PRESENT-EXACT-0 court unchanged, 3 sittings of 4 runs, and is observational first: it counts
  recurrence and cross-run drift from the two files and the host state, with no intervention.
- **LIVE-LOOP-0** is the gate that matters: the current (W, M, C) state → `LoopRenderer` on its persistent buffers →
  one frame rendered from that state → SetDIBitsToDevice → the screen witness → the next frame. It includes window
  events, clean shutdown, refusals logged and runs ledgered. The shell mutates nothing canonical. Its first court is
  narrow: no authoring input, no flip model, no persistent workers, no latency claim.
- **LIVE-INPUT-0** turns physical input into authoring operations through the authority boundary already built
  (Urðr's input membrane `cue`, frozen in `oracle/game/`, the workshop and the session model). The shell never mutates the world directly. The first
  vocabulary is tiny: move the camera, select a cell, open or close a cell, change a tile or material. It is named
  LIVE-INPUT-0 because `INPUT-0` is already seat 9. As ratified and built, the first slice is narrower still: the six
  moves and opening or closing the faced cell, with no cursor and no tile or material keys (those wait for
  LIVE-AUTHOR-0). The authority boundary it goes through is the session model: every press becomes an event in an
  in-memory SESSION-WALK log, and W and M are that log's replay.
- **LIVE-AUTHOR-0** proves the mutation/render bridge. One interaction must demonstrably go input → typed edit →
  session event → authoritative W, M change → next render → changed pixels. The control must hold too: a camera-only
  input may change pixels, and W and M stay unchanged. That preserves the W / M / C boundary the workshop already
  enforces. The test is not "I can click something" but **the thing I author is the same authority that the next frame
  renders**.
- **LIVE-SESSION-0** makes the live chain recoverable by connecting the live loop to the session walk's existing
  authority and deterministic replay, rather than inventing a second live-state system: live events → append-only
  session → checkpoint or save → restart → replay → the same world. It now comes before LIVE-AUTHOR-0.
- **Afterwards:** PRESENT-1, the live-loop re-breakdown, and BANDWIDTH-0 / POOL-0 are optimization and latency work
  measured on the real loop. They are not prerequisites for walking. PRESENT-1 starts with how the screen is witnessed
  once presentation moves off GDI: the GDI readback cannot be assumed to remain a valid witness under flip-model
  presentation, and whatever replaces it is measured before it is trusted.

Each of these rungs is ratified, preregistered and built in turn; none is claimed until its gate stands.

---

## After BEARING-FAST-0: what evidence is worth buying (the owner's ruling, 2026-10-01)

BEARING-FAST-0 is built and measured, and at the time of this ruling no live path used it; MOUSE-LOOK-0 has since
wired it into the live editor. The owner ruled that the next work is chosen by what evidence is worth buying, not by
which optimization can be imagined next. The order:

| # | Work | Why | Where it stands |
|---|---|---|---|
| 1 | BEARING-FAST-0's host speed court | Establish whether the 6,667 µs target is met. | Run: met, 3,716 µs. |
| 2 | Production promotion, only if the target is met | Do not optimize a kernel that is already sufficient. | Met: eight row bands of exact stepping is the production candidate. MOUSE-LOOK-0 wires it into a live path, not before. |
| 3 | SIM-TICK-0, mouse sensitivity and live mouse-look | The actual interaction seam, now that the renderer can support it. | SIM-TICK-0 (the rules and the sensitivity, windowless) is built, and its gate passes on the host. SIM-TICK-0a (the court's two tick rulings, windowless) is built, and its gate passes on the host. MOUSE-LOOK-0 (the real mouse and the window) is built and its gate passes on the host. `shell look-window` ran there once: the keys walked on the tick and the save verified, but no mouse report reached the loop, so the look itself is still to be shown. MOUSE-LOOK-0a (the owner's correction of a registered limit, the run's end, and the window's observation of raw input) is built and its gate passes on the host. On the second run a real mouse turned the camera: 1,761 looks on the tick, the focus lost and regained with no session event, the session's picture on the screen, and every free-heading frame equal under the reference. |
| 4 | PRESENT-1, the flip-model presentation | Renderer speed is not input-to-photon speed; LATENCY-0's evidence makes this the next presentation boundary. | After mouse-look. |
| 5 | A cross-host correctness witness for the fast path | Portability evidence, not worth delaying the interactive path unless a cross-host failure appears. | The gate's court already runs on two hosts (Linux here, the owner's Windows). A further host is deferred. |
| 6 | Benchmark regression recording | Protects a production fast path against performance regressions. | Once the fast path is in a live path. |
| 7 | A persistent worker pool (tread D) | Only if a host court shows thread creation is material. | Its trigger did not fire. |
| 8 | SIMD, structure-of-arrays and cache experiments | Candidate optimization courts: measure first. | Deferred; no gain is claimed. |
| 9 | GPU | A separate architectural branch, not the next CPU optimization. | Deferred. |
| 10 | Lean or SMT formalization | Assurance research, not a prerequisite for the renderer. | Deferred; see below. |
| 11+ | Homotopy type theory, category theory, quantum-inspired work | A research track, not the production roadmap. | Not on the route. |

The sequence is therefore BEARING-FAST-0's host court → promote or defer → SIM-TICK-0 → mouse-look → PRESENT-1 → drift
and regression evidence. The optimization staircase reopens only if a court misses its target. The trap to avoid is
optimizing a renderer that has already crossed its threshold while the actual experience (mouse timing, simulation
ticks, presentation, input to photon) stays unmeasured.

Three rulings on how claims are made:

- **No scalar scorecard.** A letter grade collapses things this repository keeps apart: deterministic correctness,
  mutation resistance, portability, host performance, presentation latency, maintainability and research maturity.
  Each claim keeps its own grade from the existing vocabulary (MEASURED, ESTABLISHED, DECLARED, DEFERRED) and its own
  `does_not_show`.
- **Outside estimates are not Verðandi's claims.** Projected gains from outside analyses, such as a "3–5× ceiling",
  "SIMD 25–50%", "GPU 10–100×" or "world-class", are hypotheses attributed to their sources until measured here. Those
  analyses are not carried in this repository.
- **Formal methods, if opened, start narrow.** A months-long mechanization of the whole studio is a research
  investment, not the next rung. The existing court (1,972 cameras, checked bounds, 14 mutations, the host speed court,
  and the live differential check to come) finishes its job first. The natural first theorem is the seam BEARING-FAST-0
  created: for every admissible row, camera and scene, the exact walker produces the same pixel inputs as the reference
  kernel.

---

## The sequenced path (named rungs only)

### LATENCY-1 — does the headroom survive the present path · **measured and confirmed** (`8e93118e`, amended `b32d226f`)
Re-run the sealed reference session through the present path *now that the render is fast*, and compare frame-ready →
composited against `LATENCY-0`'s immutable baseline. This is a **measurement, not an optimization** — it was meant to
answer question 1; the amendment below records why it cannot, and LATENCY-1R does. Off-gate, host, witnesses first, no refresh claim.
The method is hash-locked (`latency1-preregistered`): the comparator is `LATENCY-0`'s sealed **frame-ready →
composited** p99 — the *same observable*, inherited never re-derived — and **never** an emit p99 (the GAUNTLET-2
7,734 µs baseline is a different observable; mixing them is a category error). The delta reads as
headroom-propagates / presentation-dominant / shell-contention, and none of it proves input-to-photon.

**Amended before the number (LATENCY-1a, `b32d226f`).** LATENCY-0's instrument renders every frame before its window
opens and times only blit → composited, so LATENCY-1 cannot see the renderer; its delta is now read as a statement
about the presentation interval only (a 50‰ materiality bound, declared), never as render headroom or contention.

**Measured.** On the owner's host LATENCY-1's first run read DEGRADATION on a three-sample p99 tail; its confirmation
read NO MATERIAL CHANGE (p99 7,339 vs 7,318 µs). The presentation interval reproduces LATENCY-0, and the first run's
category did not reproduce (`GHOSTS.md` G10).

### LATENCY-1R — the render inside the clock · **measured twice** (`5cfb3ece`)
The question LATENCY-1 cannot answer, as its own observable: render-start → composited on the same sealed session
and GDI present, for the production render (T=8) against the single-thread reference, in a locked and a uniform
phase regime. On the owner's host, two runs: **uniform PROPAGATES** both times (composited output 3.2–3.6 ms earlier
at the median; 1,341‰ and 1,182‰), and the **locked** regime absorbed in both (0‰ and 8‰ of a ~2.7 ms render saving
got through) — its preregistered label flipped from ABSORBED to PARTIALLY ABSORBED across a zero-margin boundary, which
the confirmation record states (`GHOSTS.md` G10). The production render-start → frame-ready interval itself is
14.8–15.7 ms at p50, longer than the 13.1–13.9 ms refresh.

### FRAME-SPLIT-0 — where the ~15 ms goes · **measured and confirmed** (`739dc807`): NO SEAT, multi-component
The production render-start → frame-ready interval split into seven contiguous phases on LATENCY-1R's apparatus, the
uninstrumented envelope beside it. On the owner's host (envelope p50 15.7 ms): blit 434‰ of the envelope p99, emit
272‰, frame 251‰, bgr 139‰, the rest under 10‰ each. No phase reaches 500‰, so **no single optimization is promoted**
— the frame is multi-component after GAUNTLET-2 (`GHOSTS.md` G8). The blit (`StretchDIBits` into the half-size window,
~7.1 ms p50) is the largest component, not a seated bottleneck; how much of it is the 2:1 scaling is unmeasured
(`GHOSTS.md` G11). The confirmation reproduced the reading (blit 427‰, every share within 8‰). Any further step is a
narrower, separately preregistered measurement of a named component, not an optimization.

### PRESENT-SCALE-0 — how much of the blit is the 2:1 scaling · **measured and confirmed** (`64b263da`): SCALING MATERIAL
A diagnostic, not an optimization court: the same frame presented into a half-size (960×540) and a full-size
(1920×1080) client area, the destination the only variable. On the owner's host the blit's p50 fell from 7.76 ms to
2.19 ms at 1:1 (717‰, net of the larger copy), the non-blit phases inside the confound bound (48‰), and the envelope's
p50 from 17.1 to 11.4 ms — below the refresh at full size, above it at half. The default stretch mode is
`BLACKONWHITE`, a Boolean-AND reduction (`GHOSTS.md` G11). It names no winner: what the shell should present is a
separate court, because it changes what the window shows. The confirmation reproduced it (705‰; non-blit 33‰), on
this host and apparatus. `PRESENT-1` below stays a hypothesis for the locked regime.

### PRESENT-STRETCH-0 — does the half-size blit's cost depend on the stretch mode · **measured twice** (`f5372890`): `COLORONCOLOR` MODE MATERIAL reproduced; `HALFTONE` not reproduced
A diagnostic over the same half-size frame, with the stretch mode the only variable: `BLACKONWHITE` (the default, now
set explicitly), `COLORONCOLOR` and `HALFTONE`, in 12 blocks with the effective mode read back. Per mode against the
default it reads MODE MATERIAL or IMMATERIAL (100‰ of the default's blit), unless the court is VOID or that mode is
CONFOUNDED. It adopts no mode: each draws different pixels, so choosing one is a separate court. On the owner's host
the blit's p50 was 7.27 ms under the default, 4.42 ms under `COLORONCOLOR` (392‰ cheaper) and 4.93 ms under
`HALFTONE` (322‰ cheaper), with the non-blit phases inside the confound bound (16‰, 15‰). The confirmation, in a run
that was slower across the board (the default's blit 11.59 ms), read `COLORONCOLOR` MODE MATERIAL again (449‰) and
`HALFTONE` CONFOUNDED (non-blit 53‰). So `COLORONCOLOR` reproduced per mode, `HALFTONE` is unresolved, and the combined
label did not reproduce, which the confirmation record states. No millisecond saving is carried as confirmed.
frame-ready → composited rose by most of the saving in the first run (G7), so this is not an end-to-end result.

### ALLOC-REUSE-0 — how much of the frame is per-frame buffer allocation · **measured and confirmed** (`aaaada37`): ALLOCATION MATERIAL (reuse cheaper)
A diagnostic over FRAME-SPLIT-0's apparatus with the buffers' lifetime the only variable: allocated every frame (the
production path) or once and overwritten, the same calls and marks, the reused bytes proven equal first. On the
envelope it reads ALLOCATION MATERIAL or IMMATERIAL (50‰ of the fresh envelope), with the per-phase deltas beside and
never ruled on. The production path is unchanged by it. On the owner's host the envelope p50 fell 1.59 ms (17.29 →
15.71 ms, 91‰), with the unchanged phases at 10‰. The confirmation reproduced it (17.36 → 15.53 ms, 105‰; unchanged
phases 2‰). In both runs the saving sat mostly in bgr and emit, which is reported and not ruled on. Adopting reuse in
the production path would be its own court.

### ALLOC-REUSE-1 — the render-loop entry's adoption court · **measured twice** (`dc904a6c`): PERFORMANCE PASS in both runs, ADOPT — **LOCKED** (seat 24)
The shipped shell has no per-frame render loop (`run` renders once, `playback-window` pre-renders owned frames;
G12), so what can be adopted is an **entry contract**: the persistent-buffer `LoopRenderer` as the production entry for
any loop that renders once per presented frame. The fresh path stays the frozen reference. Correctness first, on every
gate: byte identity with the fresh path over the corpus (goldens), the adversarial cameras and the sealed session, in
three orders from poisoned buffers, with no buffer replaced. Then performance, on the host: same-run ABBA, 1000 samples
per cell, PERFORMANCE PASS iff p99(reused) ≤ 950‰ of p99(fresh) (an adoption margin). ADOPT only when the run and
`--confirm` both pass. No shipped window changes either way; a later live loop enters through the adopted entry. On
the owner's host reuse's envelope p99 was 886‰ and then 929‰ of fresh's (−2.0 and −1.8 ms), with correctness holding on
every sample, so the reading is **ADOPT**. The second run was 41% slower as a whole (G13), and in both runs the frame
waited longer at the composition by about what it saved (G7). **ALLOC-REUSE-1 LOCK** carries out the ADOPT:
`LoopRenderer` is the production entry for in-loop rendering, and every fresh render entry's call site in the shell is
pinned (`allocreuse1-lock`), so the live loop renders through it. Nothing that ships today changes.

### HOST-STATE-0 — the host's state beside a court · **landed** (`58250382`)
Record, don't control: what the OS reports about the CPU, power plan, load, memory, process, display and uptime, one
snapshot just before and one just after a court's window run. Every value is an integer or a string, a field that
fails is recorded as unavailable, and recording can never block a court or feed a rule. ALLOC-REUSE-1 is the first court
to carry it. It exists to make the next cross-run drift explainable (the +59% in PRESENT-STRETCH-0's confirmation had
nothing to be set beside), never to explain it by itself. Its first snapshots put memory pressure (96% load, 359 MB
free) beside ALLOC-REUSE-1's slower second run, with the same reported clock state and plan in both runs: an
association (G13), not a cause.

### PRESENTATION-CHOICE-0 — what the shell shows · **declared** (`4a7a32d9`)
The owner's decision: the certified picture, 1:1 (the kernel's 1920×1080 composite, pixel for pixel), in a borderless
window covering the 1920×1080 screen at (0,0). No reduction by GDI or the kernel, and no new VIEW law. The half-size
windows stay as LATENCY-0's frozen instrument, and a conforming presenter is locked after PRESENT-EXACT-0.

### PRESENT-EXACT-0 — which GDI call presents it, with the screen read back · **measured twice** (`bc910e2f`): screen exact, SetDIBitsToDevice adopted
StretchDIBits at 1:1 against SetDIBitsToDevice, the call the only variable, frames through the adopted
`LoopRenderer`. The composed screen under the window is read back and must equal the certified picture byte for byte,
after a white clear that is also read back, as a hard gate. The first check of what reaches the screen rather than
what is handed to GDI (G11). Then same-run ABBA at 1000 per cell. StretchDIBits is adopted only if its p99 is ≤ 950‰ of
SetDIBitsToDevice's in both runs; otherwise SetDIBitsToDevice, the simpler semantics. The first host attempt refused
at the readback. A probe traced it to the host's performance overlay, a translucent bar drawn over every window.
Outside that bar, frame 0 read back exact under both calls. With the overlay off, both runs read the composed screen
back exact on all checked frames (20 checks, 0 differing bytes) and read NO MATERIAL DIFFERENCE between the calls
(StretchDIBits at 1,006‰ and 1,013‰ of SetDIBitsToDevice's p99). So SetDIBitsToDevice, the simpler call, is adopted. At
1:1 the call costs about 1.8 ms, and the frame's envelope (about 10 ms at p50) sits below the refresh.
**PRESENT-EXACT-0 LOCK** (seat 25) ships it: `shell show` and `shell show-playback` present the certified frames 1:1
through SetDIBitsToDevice, read the screen back after every present, report any mismatch, keep showing, and exit 3 if
the screen ever differed.

### REFUSAL-WHY-0 — why a readback refused · **landed** (`15701718`)
When the screen read back differs, the refusal now names what lies above the window over the differing box: each
visible, uncloaked top-level window above ours that meets it, with its program, process, class, title and overlay
styles, or "below the window layer" when none does. It is appended after the verdict is decided, it reads and never
acts, and it cannot change a verdict. The first host refusal needed a separate probe run and the owner's knowledge to
be traced to an overlay. The next one names its candidates itself. A candidate is not a cause.

### HOST-STATE-1 — the reported clock and paging · **landed** (`b992d9dd`); first host look taken; no court records it yet
Version 2 of the host snapshot: HOST-STATE-0's fields unchanged, then the clock the OS computes (% Processor Performance
and % Processor Utility, uncapped, with the nominal × performance estimate) and the system's paging rates, each over a
1000 ms window. Version 1 stays the default, so no existing court's records change. It fills the two gaps G13 left: a
reported MHz that cannot show boost, and memory pressure with no paging witness. A court records it only by its own
preregistered entry. Still association, never cause. The first host look read every counter, with performance at
118.5% of nominal (boost now visible) and 1 hard fault/s at 94% memory load. Processor Frequency read 1,658 against a
2,000 maximum, so the entry's "nominal" gloss is not established, and neither is the meaning of the estimate built on it.

### REFUSAL-LOG-0 — refusals that accumulate · **landed** (`424b7c9a`)
Every refusal on the present path (the PRESENT-EXACT-0 court's and the locked presenter's, and every differing screen
readback in `show`) appends one unsealed JSON line to `build/refusals.log`: run, sequence, operation, reason code,
attribution token and context. A console line reports a refusal once. The log turns a recurring refusal into a count
across runs (`python verify/refusallog.py`). It is an observation, never evidence: not sealed, not committed, read by
no rule. The gate proves on the mock court that each refusal leaves exactly one record and each record one refusal.
Since REFUSAL-WHY-1, a screen-readback record also carries what covered the screen (below).

### RUN-LEDGER-0 — the runs, refused or not · **landed** (`ecf3fdb9`)
The refusal log's denominator: one unsealed line per court or presenter run, whatever its outcome, in its own file
(`build/runs.log`), with the run's readback counts, its refusal count and its exit code, joined to the refusal log on
`run_id`. A clean run is counted too, so a recurrence can be stated as "refused in N of M runs". It is an observation,
not evidence, and it is kept out of the refusal log, which holds only refusals.

### REFUSAL-WHY-1 — what covered the screen, accumulated · **landed** (`ac75db51`)
A screen-readback refusal record now carries the covering layer and, for each window above ours over the differing
box, its program, class, overlay flags and rectangle. Titles and process ids are never written, and the rectangle is
geometry, not identity, so recurrence is counted by program, class and flags. The console and the log come from one
walk. A recurring program over the screen is a candidate, never a cause.

### LIVE-LOOP-0 — the first per-frame loop · **measured on the host** (`65550cc0`): the first live walk exact
The sealed session walked live: 24 compositions per step and 150 held, every composition rendered through the
`LoopRenderer` from the current step, checked against that step's verified bytes and presented by SetDIBitsToDevice in
the presenter's borderless window. The screen is read back at every step and twice in the hold, and a differing screen
is counted and logged, never hidden. There is no input, no camera, no clock: counts only. The gate executes the loop
itself over the mock. On the owner's host, the first live walk rendered and presented 246 compositions, and all 6 screen
readbacks were exact. It is the first gate on the route; the authoring input that changes the state is LIVE-INPUT-0's.

### MOUSE-LOOK-0 — a real mouse on the locked tick rules · **built** (`60870497`): the gate passes on the host; a real mouse turns the camera there (the second run, under MOUSE-LOOK-0a)
The fourth rung of the owner's ladder: real mouse → 64 Hz accumulator → command → the existing live loop. By the
owner's ruling it is a new entry, `shell look-window` (and `shell look-selftest` on the mock), on the same loop
function, session, journal and seal; `shell live-window` and every earlier command stay as they were and are given no
tick source. The rules are SIM-TICK-0's and SIM-TICK-0a's and are not touched. What this rung adds is the clock (an
input's tick is the tick of the composition that drained it), the mouse (Windows raw input, the relative horizontal
count and nothing else), the capture (the cursor hidden and confined while the window is in the foreground, released
when it is not, and never an event in the session), and the loop presenting a free heading: the session's own render,
the one its witness came from, with no overlay and no second render. The screen is read back one composition in 75,
and the reference recomputes one free-heading frame in 64 on a worker thread, a difference refusing the run; the save
still recomputes every one. The gate runs the loop over a mock mouse, keyboard, focus and clock: the saved data is
byte-identical to the windowless tick run's on the same inputs at their drain times; a window out of the foreground
changes nothing in the session; the picture handed to the call is the kernel executable's; a defective fast path is
refused by its first sample. No latency is claimed anywhere. 64 ticks against 75 compositions repeats about 11
compositions in 75, and they are counted in every saved session.

On the owner's host the gate passed with the same 207 rows and rowset, the window build compiled, and
`shell look-window` ran once. The window held the foreground throughout, the mouse was captured and released once, 48
key presses were stamped by the window's clock and applied on the tick (47 events), 1,826 compositions of the
composite were byte-checked with 25 screen readbacks exact, and the session saved and verified. What the run did not
show is a look: no mouse report reached the loop, the heading never left north, and so no free-heading picture, no
sample and no free-heading certification happened on the host. The record cannot say why, because the window section
counted nothing before the point where it admits a report. The run also found that Esc destroys the window in the
pump that reads it, so the saved file labelled the run's end `closed` where the tick run says `escape`; the session
itself is right. The owner ruled that a registered limit's wording be corrected by an amendment (MOUSE-LOOK-0a), that
the one check with no row stays a sanity check, and that nothing is optimized from this run.

### MOUSE-LOOK-0a — the timing limit corrected; a run's end and the window's observation · **built** (`3778b592`): the gate passes on the host; the second host run is the execution witness
An amendment to MOUSE-LOOK-0, whose entry is not edited, registered after the first host run and reading none of its
counts. By the owner's ruling the registered timing limit is corrected: a composition applies at most one closed tick
command, `span` records the largest number of tick boundaries between consecutive compositions, and a span above 1
means the loop fell behind the tick schedule, not that several commands were applied. From the host run: Esc destroys
the window in the pump that reads it, so the loop ends there, the tick still open is applied, and the run is recorded
as ended by escape; the mock now closes its window at an Esc as the host's does. And the window section counts every
raw input message before it reads it, every read that was not a mouse report and every report with no horizontal
count, and the run prints that observation, because the first run could not say whether raw input had arrived at all.
The read itself no longer requires an exact size. Nothing is optimized from the first run.

On the owner's host the gate passed with the same 209 rows and rowset, the first run's session was sealed (holding no
look), and `shell look-window` ran a second time. The observation adds up: 14,867 raw input messages, 13,931 of them
relative reports with a horizontal count and all admitted, none unread. They became 1,761 looks, at most one a tick;
with them 14 moves, 57 sensitivity changes across multipliers 1 to 14 and both steps, and a held W walking once a
tick. The window left the foreground once and came back, the mouse released and recaptured, and the session holds no
event of any kind for it. Of 4,649 compositions 4,541 presented the session's own picture; 62 screen readbacks, none
differing. The reference agreed at all 27 samples during the run and at all 1,775 free-heading frames at the save,
and the workshop built in the container recomputes those 1,775 frames from the saved file and reaches the same head:
the production tread on Windows, the reference kernel on Linux. Esc ended the run, recorded as `escape`. The owner
sealed the session on his host (`livesession-DANIELDILLBERG-b28e42be62c4.json`). Counted and
not interpreted: 4,649 compositions against 5,470 ticks, 2,852 repeating the picture before them, a span of 6. The
run does not decide why the first run had no mouse report. No latency is claimed. The owner's report of the run: the
look worked, and only horizontally. That is the registered scope (the carried camera turns in heading alone, and the
936 raw reports with no horizontal part were counted and not used); a camera that looks up and down has no frozen
oracle yet and is not on the route until the owner rules it there.

### SIM-TICK-0a — sensitivity as a typed configuration event; held keys by the tick · **built** (`471f4d72`): the gate passes on the host
MOUSE-LOOK-0's court (2026-10-02) gave four rulings. Two are about the window and wait for it: the mouse is captured
until Esc, and that capture is shell state that never enters the session, so a focus change makes no event; and every
64th free-heading frame is recomputed by the reference off the loop. The other two are rules of the tick, and the
owner's own separation (rules first, with no window in the proof) puts them here, in an amendment to SIM-TICK-0 whose
entry stays unedited. First, a sensitivity change is a typed configuration event: PgUp, PgDn and Tab are the physical
binding, their effect is what the session records, and it takes effect at the next tick. The event carries the
configuration after it and its tick, has no witness and is not folded, because the head is the worldline's and a
setting is not part of the world; the session replays the configuration by one legal transition at a time, and a
look's inputs must carry the configuration in force. Second, HOLD-WALK-0's law takes the tick as its unit: a fresh
press always acts, the first repeat of a held key in a tick walks, later ones are coalesced and counted, and a repeat
of any other key is ignored. The gate drives both with scripts: the owner's own sequence (PgUp, mouse, Tab, mouse,
PgDn), eight forgeries each refused by both verifiers, a crashed run whose configuration comes back from its journal,
and a held walk whose saved data is byte-identical to the same walk pressed. Mutation testing found the configuration
row's first form unable to catch one removed check, and the row was strengthened before it counted. On the owner's
host the gate passed with the same 201 rows and rowset as here. One informal timing was taken there to size
MOUSE-LOOK-0: a windowless run of 640 looks took 13.26 s in all, 20.7 ms per look summed over the live render and
journal, the reference's recomputation at save and the saved file's replay. It bounds each of those and separates
none of them; it is an observation of one run, not a record.

### SIM-TICK-0 — the mouse-look rules as integer law, windowless · **built** (`dc1dddf2`): the gate passes on the host
The third rung of the owner's ladder, and deliberately half of the work: the owner ruled that the rules are locked with
no window in the proof, and that the real mouse comes after, as its own rung. The boundary is raw input → tick command
→ SESSION-WALK → authority. A tick is exactly 15,625 µs (64 Hz). A tick's mouse reports are summed and applied once, as
one look; then its keys apply in arrival order. The look's delta is counts × multiplier × step, in integers: the
multiplier a whole number from 1 to 64, the step 88 heading ids or 1. W, A, S and D step toward the heading's nearest
cardinal, ((k + 45000) div 90000) mod 4 with the tie clockwise, and never turn. The one live session gains one event, a
look, witnessed by the frame at the new heading: the facing kernel's at one of the four anchors, as before, and the
bearing kernel's anywhere else. A tick run saves each event's tick and each look's inputs beside the event; the tick
is recorded and is never authority. Live, a frame at a free heading is rendered once by BEARING-FAST-0's production
tread; at save every such frame is recomputed by the reference across threads, and a session is saved
reference-certified or not saved. The gate drives it all with scripted inputs and integer times: the laws are checked
exhaustively over the 360,000 heading ids against a Python re-derivation, one script exercises the boundaries and the
refusals, the saved session's frames are checked against the kernel executable and by the workshop's verifier, and a
shell with a planted defect in its fast path is refused at the save. One thing was found while building: an index
frame can be the same at two neighbouring headings, so a look folds its camera token together with its witness; the
registration was revised for that before it left the build machine. On the owner's host the gate passed with the same
197 rows and rowset as here. The window build, which the build container could only type-check, compiled there, and a
walk of 46 moves in the live editor rendered, presented and byte-checked 1,034 compositions with 50 screen readbacks,
none differing, and saved and verified as before. That walk held no look: nothing here reads a mouse, a clock or a
window, and nothing here says how it feels.

### BEARING-FAST-0 — the bearing camera made fast, held to the reference · **measured on the host** (`f0a9a57d`): the target met, the sweep exact
One rung with its staircase inside, as the owner ruled. The reference spent its time in per-pixel 128-bit division;
the fast path, `kernel/bearingfast.rs`, keeps the reference's traversal and walks the floor and the walls exactly in
64-bit integers instead: along a row the floor point moves by a fixed exact step per column at any heading (scanline
floor casting, made exact), and down a wall column the texture moves by a fixed step per row, with one 128-bit setup
per row or column. The frame and the picture are written in one row-major pass (tread A); tread B reads the floor from
the blocked layout LOCALITY-0 locked; tread C runs eight row bands on threads. Every tread is the reference byte for
byte at 1,972 registered cameras on every gate, also in a build with overflow checks on, and every narrowing from 128
to 64 bits is checked and bounded. On the owner's host a speed court keeps a tread only by its margin and names the
production candidate against the target, a p99 of at most 6,667 µs (half the 75 Hz refresh), and a sweep checks it
against the reference at every walkable cell at every whole degree. On the owner's host the gate passed with the same 189
rows. The speed court promoted A (7,042 µs worst-camera p99 against the reference's 59,901) and did not keep B (the
blocked floor did not pay single-threaded). It kept C over A's layout: eight row bands at 3,716 µs, under the 6,667 µs
target, so the staircase stopped there with D never needed. The sweep then checked that production tread against the
reference at all 622,440 frames, and every one was equal. Renderer time only; the next measurement on the route is the
present and the input path.

### BEARING-0 — the bearing camera carried, its reference kernel placed · **built** (`de19660f`): the gate passes on the host
The first rung of the owner's mouse-look ladder on this side. Urðr earned the turning camera as VIEW-YAW-0 and froze it
as `urdr-oracle-2`: a heading is an integer id in [0, 360000), millidegrees clockwise from north, naming one primitive
Pythagorean triple, so the renderer consumes exact rational directions and never an angle; the four cardinals are
anchors equal to the frozen frames. BEARING-0 carries the record and its table verbatim (`oracle/urdr-oracle-2.json`,
`oracle/bearing_octant.txt`) and places the reference kernel, `kernel/bearing.rs`, the tag's Rust placement with only
its visibility changed. The camera is (cell_x, cell_z, heading id), the id authoritative and never normalized; the table
is compiled in and refused if it does not match its pin. The gate recomputes every digest the record states from the
record alone, and the reference reproduces all 104 witnesses of urdr-oracle-2 bit for bit. At the four anchors it is
the facing kernel, and dropping the hypotenuse from the depth moves every non-anchor frame. It is the correctness court
for BEARING-FAST-0 and drives no window: the shell, `mantle.rs` and `fast.rs` are unchanged. Its speed (about twice the
facing kernel's single-thread time, measured off the gate here) is why mouse-look waits for the fast path. The owner's
rulings for the rungs after it, recorded in RUNGS.md, are a 64 Hz tick, W/A/S/D toward the nearest cardinal (ties
clockwise, never changing the heading), and an integer sensitivity multiplier on a step of 88 or 1 ids, saved in the
session. On the owner's host the gate passes with the same 183 rows and rowset as here. Its first run there failed one
row, `oracle2-frozen`, on a working copy of `urdr-oracle-1.json` checked out with Windows line endings before
`.gitattributes` existed. That hash was pinned in the docs and enforced by no row until this one. The file was
re-checked out and the row kept strict.

### HOLD-WALK-0 — holding a key walks the live editor; the world stays discrete · **measured on the host** (`c03260a2`): a held walk saved and verified
The live editor, `shell live-window`, now walks while a key is held. W, A, S, D and the arrows are the held keys: the
steps and the quarter turns, so holding A or D looks around. A held key's auto-repeat is bound as its move and appends an
ordinary move event, at most one per composition. Later repeats in the same composition are coalesced: counted, never
an event. A fresh press is never coalesced, and holding Space, Q, E or a class key acts once. The keyboard's repeat is
the only speed source: the shell keeps no clock, reads no key-up and carries no key state between compositions. The
gate proves the held set, the one-per-composition cap with its coalesced count, and that a held walk saves exactly the
data the same walk pressed would. LIVE-INPUT-0's and LIVE-SESSION-0's commands still bind no repeat. On the owner's
host the gate passes with the same 174 rows, and a held walk (31 repeats, each walked, every readback exact) was saved
and verified; pressed instead, the same walk reaches the same head. The owner judged held keys over the grid not to be
the free movement he wants, so that route item is open.

### LIVE-AUTHOR-0 — the thing authored is what the next frame renders · **measured on the host** (`9a3e4521`): tile classes painted live, saved, and resumed
The one live editor, `shell live-window`: LIVE-SESSION-0's durable loop under the authoring binding, which is
LIVE-INPUT-0's keys plus 1–5 for the tile classes wall0–wall3 and floor. A class key paints its class with the next
colour of a registered 8-colour palette, read from the session's own M, as one `tile:CLASS,R,G,B` session event. It is
commit-only: nothing is shown before the edit is appended, and the shell holds no colour of its own. The frame witness
does not see colour, so the picture is witnessed per state by the reference composite's sha256. The gate proves the
camera control condition (a turn changes the pixels while W and M stay the same) and its converse (a tile edit changes
M, leaves W alone, and changes the pixels exactly when its class is on screen). It also proves the painted world
persists: a resumed session's first picture is its parent's last. On the owner's host the live editor walked, resumed a
saved session and saved a verified continuation. A later walk painted all five classes live: 28 tile edits by class
keys, each the palette's next colour, every one of 62 readbacks exact. It was saved and verified there, and here its
file verifies unchanged. The same presses replayed here reach the same head, and the level's bytes are unchanged by
the edits. The painted session was then resumed on the host as LOAD, walked and painted further (two more edits),
and saved as a verified child whose lineage names it, every readback exact.

### LIVE-SESSION-0 — the live session made durable and recoverable · **measured on the host** (`70086a72`): a saved walk and its resumed continuation
LIVE-INPUT-0's loop, unchanged, over a session whose every appended event is journaled: one record per line with its
length and sha256, each flushed before it counts. Esc seals the session in the workshop's own session-walk format by an
atomic replace. The shell then reads the file back and verifies it before the run counts as saved; a seal that fails is
a refusal, never a quiet exit. `--resume` continues a saved session, or recovers a crashed run from its journal, into a
new file whose log begins with its parent's. Loading checks integrity, then the renderer identity (a hash of the render
sources), then replays and classifies: an identity mismatch alone is never corruption, and only replay decides. Saved
sessions live in `build/sessions/` (gitignored). `verify/livesession.py` seals one as a committed record that shell
playback and the workshop both replay. The keyboard-focus observation is recorded, never ruled on. On the owner's host
the first saved walk (37 events, 4 of them edits, every one of 99 readbacks exact) was saved and verified there. Its bytes
verify unchanged on another machine through the workshop's own sessionwalk, with the same renderer identity. It was
then resumed and walked on (197 more events, ended by Esc) into a new file whose lineage lies on its own chain, and the
parent was untouched. A crash recovery on the host is still to come.

### LIVE-INPUT-0 — key presses feed the session the live loop renders · **measured on the host** (`f81c2cf1`): the live session walked and edited by key presses
Walking plus open/close. Arrows or WASD walk and turn, Q and E strafe, Space opens or closes the cell one step ahead of
the camera (rock to floor, floor to rock; a stair is not toggled), Esc ends; an auto-repeat is never bound and any
other key is ignored. Every press becomes an event in an in-memory SESSION-WALK log, validated as the workshop
validates it. W, M, the camera and the head are that log's replay, private to the session, so the shell never writes
the world. Every composition is rendered through the `LoopRenderer` from the session's current state and presented,
and the screen is read back after every change. The gate proves the binding on two key scripts and replays each
script's log through the workshop's own SESSION-WALK to the state and head the loop reached. Nothing is saved; that is
LIVE-SESSION-0's. On the owner's host, key presses walked the live session and opened and closed cells in it. An
opened cell was walked through and a closed one blocked, Esc ended the session, and every screen readback was exact.
Each walked log, replayed through the workshop's own SESSION-WALK, reached the head the loop printed. The deciding walk
was fixed beforehand as the gate's script A. It diverged at one press (S typed for Space), so its predicted head was not
reached; the walk as typed replays exactly. A refused edit was not exercised on the host. In the first run no key press
arrived, and why is not established.

### DRIFT-0 — variation within and between runs of the same workload · **preregistered** (`d445dcf9`); sitting 1 of 3 complete (4 of 12 runs)
Observational: the locked PRESENT-EXACT-0 court repeated without modification, 3 sittings of 4 completed runs (60 s
between runs, 4 h between sittings), with the owner's declared overlay state and HOST-STATE-1 before and after each
run. Refused runs are sealed and kept. The report is a panel: each run's p50, p95 and p99 per call, its within-run
spread and host state, and the between-run spread within and across sittings, with the two earlier PRESENT-EXACT-0
runs beside it as history. No verdict, no threshold, association never cause. It gives the next decision an empirical
basis for G13's drift.

### PRESENT-1 — decouple present from refresh (LATENCY-1R measured the coupling absorbing the render headroom in phase)
`LATENCY-0` *established* only that the composed-GDI present costs at least one refresh interval. `PRESENT-1`'s
falsifiable hypothesis — to be measured, never assumed — is that a **flip-model / waitable-swapchain** present can
decouple present latency from refresh. The prior art is well documented: the DXGI flip model shares frames directly
with the compositor with minimal copies, a frame-latency waitable object reaches ~1 frame of latency in Independent
Flip (and lets the DWM sleep), and `ALLOW_TEARING` with multi-plane overlay goes lower still. Built std-only against
raw Win32/COM (as `win32.rs` already hand-rolls GDI); off-gate; `HARDWARE-144` additionally needs a ≥144 Hz panel.

**Ordered after the live loop, and held as hypotheses until measured here.** The flip model's benefit is for a loop
that renders every frame, so PRESENT-1 comes after the live loop below and is measured on it, not on the pre-rendered
presenter. Until then, four things stay hypotheses for this shell. The borderless 1:1 geometry makes Independent Flip
*eligible*, which is not proof that Windows will use it. A waitable swapchain's latency is documented behaviour, not
evidence about this shell. A flip swapchain takes only 32-bit formats, so the blit-hash law needs a 32-bit carrier
first. And the screen witness must be re-established under the new path: the GDI readback is established only for the
GDI presentation it was measured on, and whether another capture path (for example Desktop Duplication) gives an
exact witness there is itself to be measured.

### Interactive capture — the inverse of SHELL-PLAYBACK
Raw window/device event → binding → typed action/edit → `SESSION-WALK` append → the *same* sealed representation that
headless authoring produces. `SHELL-PLAYBACK` already proves a sealed session replays to the exact window frames;
interactive capture closes the loop so a *live* edit produces a sealed session that would replay identically. A
shell/input problem, not a new authority — measured against the existing session machinery, never modifying it. The
industry pattern to borrow is the **authoring-data / runtime-data split** (e.g. Unity DOTS), with deterministic step
and reload atomicity — which is exactly the workshop's edit → authority → record shape. The live loop this needs is its
own rung (timing, cadence, ownership, input). ALLOC-REUSE-1 read ADOPT and is locked, so that loop renders through
`LoopRenderer` rather than deciding its allocation again. It presents through the locked 1:1 presenter's call and
reads the screen back as that presenter does. It is LIVE-LOOP-0 in the route above, ahead of PRESENT-1, and its first
court is kept narrow: the loop itself, without live editing, input, the flip model or latency claims. After it, and
after any change of presentation path, the frame's breakdown is re-measured rather than carried forward. Interactive
capture itself is LIVE-INPUT-0 through LIVE-SESSION-0.

### SEMANTIC-0 — a float-free, geometry-bound semantic layer
New VIEW semantics the studio did not inherit (filtering, variety) earned by a Verðandi-local reference pinned by
rows here, as the HUD's pins are — CORE semantics have one route only (Urðr, re-frozen). This is the rung that lets
the world mean *more* than the frozen oracle certified, without ever letting the shell mint that meaning.

### MERGE-0 — deterministic, consensus-free merge of non-conflicting edits
Combine two authored branches of a world with a merge that is commutative, associative and idempotent, **stripped of
consensus and wall-clock** — the join-semilattice discipline of conflict-free replicated data types, but applied to
an authored, hash-chained edit history rather than a live distributed store. The prior art (state-based and
delta-state CRDTs; deterministic lockstep simulation) supplies the convergence theory; the Verðandi constraint is
that the merge must produce a *sealed, replayable* history whose result is byte-identical regardless of merge order.

### LLM-BUILDER-0 — the living proposal machine · **declared** (the owner's goal, 2026-10-02); not registered, nothing built
The owner's stated goal for what a language model may be in this studio. It is recorded here before any of it exists,
so that the rungs built before it are built in respect of it. The law:

> **The model may propose becoming; only the verifier may admit it.**

The model is not a programmer inside the runtime. It is a proposal engine working against a sealed worldline, and it
stays outside canonical authority. Four things are kept apart:

```text
IMAGINATION    the model                  "what could change?"                 untrusted
ADMISSIBILITY  the verifier               can refuse; never proposes
AUTHORITY      the session, the workshop  the admitted event, in order
CONSEQUENCE    the kernel, the reference  the frame and the digest it produces
```

```text
model ──► PROPOSAL (typed, bounded, anchored) ──► VERIFIER ──► refuse
                                                      │
                                                  admissible
                                                      ▼
                         SESSION EVENT ──► ordered replay ──► candidate W, M
                                                      │
                                              reference witnesses
                                                      ▼
                                                   COMMIT ──► the new worldline
```

- **A proposer, not an authority.** The model's output is a typed proposal: a target, an operation, its parameters, the
  session head and the authority digest it was made against, and its provenance. It may say "at this exact worldline,
  open cell (28,27)", and later "create a corridor generator with these declared parameters". It may never say "here
  is some code; run it inside the renderer". Arbitrary live code is not the primitive. That distinction is what keeps a
  second authority out.
- **The worldline anchor.** A proposal is born at a session head, an authority digest, a renderer identity and its own
  digest. It proposes what, from exactly here. If the live session has moved on before the proposal is admitted, the
  verifier does not guess whether it still applies: the proposal is rebased explicitly or it is refused. There is no
  silent merge across time. A proposal has no authority until its ancestry is proven.
- **Speculation is an object.** A preview is not a hot swap. It is a speculative worldline: a candidate authority
  replayed from the proposal's anchor, rendered as much as is needed, and never touching the live world. One preview
  frame serves interaction and certifies nothing. Certification asks for the witness set the proposal's kind calls
  for: the authority's validity, targeted falsifiers, the reference's frames, replay from the anchor, exact digests
  where they apply. Only then does the branch become history.
- **The prefix is sacred.** The model appends becoming. It never rewrites what has become. The sealed history is a
  prefix of every continuation; a stream of events is concatenated, never permuted.
- **The commit envelope.** An admitted proposal is recorded with more than an action: its id, the parent head, the
  base authority digest, the proposal's digest, the operation and parameters, the provenance, the verifier's identity,
  the verification witnesses, and the resulting head and authority digest. The model's text is provenance, not
  authority. The authority is the verified typed event, so the session replays the same with the model gone.
- **How it grows.** From "turn this cell into a door" to "generate a corridor", to "author a new material", to
  "propose a new deterministic gameplay mechanism". Each step asks for stronger verifier laws. None gives the model
  more privilege in the runtime.

The sentence the owner would put in the charter: **Verðandi does not execute what the model writes; it records what
the verifier admits.** It stands beside the charter in the README as a declared goal. The ratified charter block is not
edited.

### LLM-BUILDER-0, continued — program time and content time; the design-event stream · **declared** (the owner's, 2026-10-03), and by his ruling what the route builds towards; not registered, nothing built
Two design texts the owner brought on 2026-10-03 and asked to have recorded. Both are replies to his own description
of what he is after, so their wording is quoted where it states the rule and summarized elsewhere. They extend
LLM-BUILDER-0 above and change nothing in it. Nothing here is built, and no rung is seated by it.

**The owner's ruling (2026-10-03): this is what the studio builds towards.** He brought the two texts again with
those words. That makes them the route's destination and not only a record. It seats nothing by itself: each rung
towards it is still chosen in its own court, registered before it is built, and held by rows. The four rules listed
at the end of this section still want their rulings first.

**1. The gate certifies the program. Content is admitted, not gated.**

> **The engineering gate certifies the program. The content admission layer certifies that an artifact conforms to
> the already-certified program. Content generation does not invoke the engineering gate.**

```text
PROGRAM TIME    source ──► GATE ──► certified build            runs when the program changes
─────────────────────────────────────────────────────────────────────────────────────────────
CONTENT TIME    prompt ──► proposal ──► CONTENT CHECK ──► admitted artifact ──► the certified runtime
                                                                        runs when the world changes
```

- **`GATE`: engineering certification.** It answers questions about the program: is the kernel deterministic, does
  replay reproduce, does authority stay apart from presentation, does the fast renderer equal the reference, do the
  seams hold. It runs when the kernel, the renderer, the authority, the session's semantics, the workshop's
  semantics, an optimization or the shell's architecture changes: a targeted gate, then the full gate, then a
  certified build.
- **`CONTENT CHECK`: artifact admission.** It answers questions about one piece of content: is its form valid, are
  its coordinates in bounds, do the things it refers to exist, are its constraints satisfied, does it load without
  breaking the runtime's contracts. It runs when the world changes: a new landscape, a building, a material set, a
  generated scene. It is meant to be fast, and it does not rerun the architectural certification.
- **What a model may do.** In the text's words: *AI may generate content freely, but it may not redefine the laws
  under which content executes.* A model asked for a landscape produces a bounded content description. It does not
  write kernel code. A change to the laws is a new program build, and that is the gate's business, not content
  generation.
- **Why it is written down now.** Without the line, new features leak content generation back into the expensive
  certification loop, and the verification architecture becomes the bottleneck of creation. The text's phrase: the
  engineering gate is *the constitution of the design environment, not the toll booth every time someone creates a
  mountain.*

**2. Conversation as the editor, over a semantic world-edit stream.**

> **Language can propose. The verifier admits. The session records. The kernel renders.**

```text
human ──► LLM designer ──► intent ──► design IR (a bounded world diff) ──┬──► speculative branch ──► fast preview
              ▲                                                           └──► verifier ──► admitted DESIGN EVENT
              │                                                                                   │
        world context (queried, bounded)  ◄──────────────  world authority  ◄──  SESSION  ◄───────┘
```

- **Intent, not code.** The model translates "make the valley narrower, raise the cliffs, put a road through the
  bottom" into typed operations on named targets. It designs transformations. It is not the authority that executes
  them, and it never edits files or reloads a renderer.
- **A spatial vocabulary.** The model does not think in files or pixel coordinates. The world offers regions,
  features, materials and structures by name, and an instruction becomes a relationship between them (above, facing,
  within a distance), which the verifier resolves.
- **Persistent identity.** Every generated object has a stable name, so "move the tower I added earlier" names one
  thing, across hours of conversation.
- **Every action a reversible transaction.** An edit carries its parent world, the intent, the proposed diff, the
  objects it touches, the resulting world and a preview frame. Undo is another event, a semantic inverse or a
  compensating edit; nothing is rewritten.
- **Preview before authority.** A proposal's first result is a speculative branch, fast and disposable. Only "keep
  it" appends it to the authoritative session. Preview is not authority.
- **Three speeds.** The fast path (prompt, proposal, diff, speculative projection, render), the commit path (accept,
  typed session event, authoritative world, save), and the engineering path (source change, gate, certified
  program), which is rare. Hundreds of accepted edits never invoke the gate.
- **A world microscope.** The model can query bounded context (the camera, a region, an object, a material, its
  neighbours, recent edits), so a proposal is made from the world's actual state and not from the words alone.
- **Why did you change that.** Every edit keeps its intent, its proposal, the operations accepted and refused, the
  objects affected, the parent and resulting digests and the model's provenance. The answer comes from that record.
  The world's provenance is authoritative; the model only reads it.
- **The design event.** An `AI_PROPOSAL` never mutates authority. It goes to the verifier, and what the verifier
  admits is a design event in the session, beside edits, moves and looks.
- **Branches.** "Three versions of this coastline" are three branches of one world, each previewed. "The cliffs from
  B, the vegetation from C, the road from A" is an explicit merge of typed events.

The endpoint the text describes is a creator who says what a place should be and watches it change, and never thinks
about source files, compilation, hashes, verification scripts or restarts, while every accepted change underneath is
typed, bounded, provenanced, reversible, deterministic and replayable. Its last line: *a world can be continuously
invented without continuously rebuilding the machine that knows how worlds work.*

**What already stands on each side of the line.**

- **Program time.** The gate is `verify/verify.py`. It runs when a patch lands in the repository. No session event has
  ever invoked it.
- **Content time, as far as it exists.** A live session is content: typed events over W and M, appended by keys and
  a mouse. On the owner's host one run appended 1,832 events with no gate between them. A saved session is admitted
  by checks on the artifact alone: its seal, its base, the fold of its witnesses, and its replay by the shell, the
  workshop and the sealer. That is the studio's content check today, for the one kind of content it has.
- **What LLM-BUILDER-0 already declares.** The typed, anchored proposal; the speculative worldline; the sacred
  prefix; the commit envelope; no silent merge across time.

**What does not exist.** A model in the tree. A proposal format. A verifier for proposals. An intent compiler or a
design IR. Regions, features, structures, vegetation, heights or any named object: the world is a grid of cells (W)
and five tile classes (M), and the renderer draws exactly that. Object identity. Branches, previews or merges. A
content package, or a check for one. The examples in the texts (a valley, cliffs, a coastline, a village) are far
beyond what the frozen oracle certifies.

**Where it meets rules already in force.** Each of these wants the owner's ruling before a rung is seated.

- **Commit-only.** LIVE-AUTHOR-0 forbids showing a change before it is appended, and this roadmap keeps previews and
  gizmos off the route because that is where a shell starts to hold an alternate authority. A preview is admissible
  only in the form LLM-BUILDER-0 gives it: a speculative worldline, itself a typed log replayed from an anchored
  head, never state the shell holds.
- **Earn the authority.** Terrain, heights, vegetation and structures are new CORE semantics. By the rule below they
  come only from Urðr, carried or earned there and re-frozen. A content vocabulary cannot be minted here.
- **How light a content check may be.** Today a session at a free heading is saved only after the reference has
  recomputed every one of its frames. A lighter check for new content kinds has to say which witnesses that kind
  needs, as LLM-BUILDER-0 already asks, and may not become a second, weaker verifier beside replay.
- **Merging branches.** A merge is an explicit, typed, anchored event, or it is refused. There is no silent merge.
- **The charter.** The first text says this boundary should become a charter-level rule. The ratified charter block
  is not edited. The rule stands beside it in the README as declared, and ratifying it is the owner's to do.

**What it would stand on, already built.** Each of these is a rung with rows, and none was built for a model.
WORKSHOP-1's session has `propose` and `commit`: a proposal is validated against the current authority and writes
nothing, and a refused one leaves the log and the head unchanged. WORKSHOP-0 refuses a record whose projection is
stale under a moved authority. SESSION-WALK is one ordered log of typed events folded to a head, verified by replay
without its author. LIVE-SESSION-0 seals a continuation as a new file whose log begins with the parent's events, never
modifies the parent, and refuses a lineage that is not on the session's own chain; it also names the renderer
identity a session was made under. SIM-TICK-0 keeps what is recorded about an event beside it and out of the head (the
tick, the inputs), which is where provenance would sit, and it certifies a session with the reference before it saves.
The carried game layer's input membrane (GAME-0, `cue`) proves its binding is a homomorphism over concatenation, with
refusal atomic for a batch: appended streams compose, and nothing there licenses reordering.

**What does not exist.** No model is anywhere in this tree, and none is a dependency. There is no proposal envelope,
no proposal digest, no anchor check against a live head, no rebase, no speculative worldline as an object, no verifier
law beyond the validation each edit already gets, and no vocabulary above a cell edit, a tile edit, a move and a look.
MERGE-0, above, is still unbuilt, and an explicit rebase would lean on it.

**What it asks of the rungs before it.** These are constraints on the route as it continues, not new work. Every new
event kind stays typed, validated by the session before it is appended, and replayable without whatever produced it.
What is recorded about where an event came from sits beside the event and is never folded into the head. Nothing but
the session's own replay writes W or M. No rung adds a path that executes text.

**Grade.** DECLARED: all of it. Nothing here is established or measured. **does_not_show.** That a model can author
anything useful here; that any verifier law beyond today's edit validation exists; that speculation, rebase or the
commit envelope work; any safety property of a system that includes a model. When it is seated it registers its own
hypothesis, failure condition and limits, like every rung.

### ADMIT-0 — the admission seam · **measured on the host** (`bdd38593`): the gate passes there, and the first admission is sealed
The first rung towards the design-event stream above. It was chosen in court, then researched, then reviewed by the
owner, then taken to a second and a third court on the questions the review left, and then registered. This section
records the first court, what the research found, one observation made here while checking it, the review, the
second and third courts, the registration and the owner's acceptance of it. It has since been built: what was
built, the nine rows that hold it and what they do not show are in [`verify/RUNGS.md`](../verify/RUNGS.md). On the
owner's host the gate passes with those rows (218 in all, rowset `0b423b279a40c85c`), and one proposal was admitted
to the session of the second `look-window` run: a wall cell opened, the head the one computed in the build container
beforehand, the saved data block byte-identical to the one saved there, the same bytes refused as stale when offered
to the child. The child is sealed as `livesession-DANIELDILLBERG-a0861e0e837b.json`. By the owner's order the next
rung is `READER-COURT-0`.

**The court (2026-10-03).** Three rulings.

- **The first rung is the admission seam.** Windowless. A typed, anchored proposal read from a file is refused or
  admitted by a verifier, and an admitted one becomes an ordinary session event with its envelope beside it. Only
  today's vocabulary: open or close a cell, repaint a tile class. No model in the tree. No gate at content time.
- **A stale anchor is refused, always.** The refusal names both heads. Rebase is a later rung. LLM-BUILDER-0 says a
  stale anchor is "rebased explicitly or refused"; this rung takes the second half only.
- **The charter: beside it for now.** The ratified block is not edited.

**What the research found.** The owner asked for a varied search for hardenings. These are outside sources and
attributed hypotheses, not claims of this repository; the links are under Sources below.

- **Recognition.** LangSec's rule is that input is a formal language, recognized completely before anything acts on
  it, kept as simple as the job allows, and read by equivalent recognizers at every endpoint. Bishop Fox's survey of
  JSON parsers found them disagreeing on duplicate keys, on invalid Unicode (two different keys collapsing into one),
  and on numbers too large to represent, and advises a fatal error for each and never re-serializing input that was
  already validated. RFC 8259 itself only says names should be unique and calls behaviour unpredictable otherwise
  (section 4), and says the same of unpaired surrogates (section 8.2).
- **Binding.** A 2026 preprint on canonicalization failures (Brömme) names the class: a digest binds bytes while the
  system compares meanings, so one meaning with two encodings, or one encoding with two meanings, breaks the binding.
  Its rule is one accepted form, with the others refused and not normalized. Trail of Bits adds that hashed fields
  must be encoded unambiguously and that digests with different purposes carry different tags. RFC 8785 (JCS) gets a
  canonical JSON only by first requiring unique names and bounded numbers.
- **Authority.** The agent design-patterns paper (IBM, Invariant Labs, ETH Zurich, Google, Microsoft) and CaMeL
  (Google DeepMind) both constrain the system and not the model: what a model emits selects among actions a
  deterministic layer already permits, and never decides them. The de Bruijn criterion from proof checking is the
  same shape: anything may propose, and a checker small enough to inspect decides. JSONSchemaBench found
  schema-constrained decoding enforced unevenly across frameworks, and conformance to a schema is not validity
  against a world.
- **Agreement between implementations.** Fluffy (OSDI '21) found consensus bugs in Ethereum's most used client by
  running independent clients on the same adversarial inputs and comparing results. Independent implementations are
  an oracle when they are actually run against each other.
- **Anchors.** EventStoreDB appends against an expected version and refuses a mismatch, and its documentation says
  idempotence is not guaranteed when the expected version is waived. An event-store survey gives the same advice on
  conflict: refuse, and let the caller decide again from the new state.
- **Crashes.** ALICE (OSDI '14) found 60 crash vulnerabilities in 11 applications, among them Git, Mercurial and
  LevelDB. The recurring mistakes were assuming an append is atomic, assuming operations persist in order, and not
  flushing the directory. On Windows, Microsoft documents `MOVEFILE_WRITE_THROUGH` as a flush promise for a move
  performed as a copy and delete, says nothing there about atomicity, and marks `ReplaceFile`'s write-through flag
  as not supported.
- **Generated worlds.** A 2025 level-generation paper (Xu et al.) has the model write constraints in a small
  description language and a solver place the level, and still reports that not every generated level is valid in
  simulation. Agentic PCG shows its agents repeating failed edits before changing approach. Both separate proposing
  from placing, and neither repairs its way to a guarantee.
- **Not acted on.** Microsoft's raw-input documentation recommends buffered reads for high-frequency mice. The
  owner's ruling stands that nothing is optimized from the first host runs; this belongs to the latency rung.

**One observation made here (OBSERVED, outside the gate).** The saved form is read by a small JSON reader in
`shell/playback.rs`, byte-identical in `workshop/sessionwalk.rs` and `workshop/session.rs`. The sealer,
`verify/livesession.py`, reads the same files with Python's `json.loads`. The Rust reader was compiled alone from
its source lines and both were given 19 hostile inputs.

| input | the Rust reader | Python's `json.loads` |
|---|---|---|
| two equal keys | accepts, keeps the last | accepts, keeps the last |
| bytes after the value | accepts | refuses |
| a second object after the first | accepts the first | refuses |
| a leading zero (`007`) | accepts as 7 | refuses |
| a string ending at a backslash | panics | refuses |
| a `\u` escape cut short | panics | refuses |
| an escaped surrogate pair | accepts as two U+FFFD | accepts as one character |
| two keys differing in a lone surrogate | accepts as one key | accepts as two keys |
| a raw newline in a string | accepts | refuses |
| `\b` and `\f` escapes | refuses | accepts |
| an integer beyond 64 bits | refuses | accepts |
| a fraction (`1.5`) | refuses | accepts |
| `NaN` | refuses | accepts |
| a lone minus | refuses | refuses |
| empty input | refuses | refuses |
| a byte-order mark | refuses | refuses |
| a NUL byte in a string | accepts | refuses |
| 20,000 nested arrays | accepts | raises a recursion error |
| 2,000,000 open brackets | aborts on stack overflow | raises a recursion error |

The two differ on 12 of the 19. They agree on four, and on one of those, the duplicate key, both accept silently.
On the other three the Rust reader does not return a verdict at all: two panics and one abort.

**does_not_show.** That any sealed record or saved session is wrong. The shell writes the saved form itself, both
seal checks pin the file's last bytes, and the heads are recomputed by replay. The reader was run alone, not
through any command of the shell, so how a panic surfaces there was not observed; no panic hook was found in
`shell/`. The harness is not in the tree and no row holds any of this. It is where the reader court below starts.

**The owner's review (2026-10-03).** A reply to the research, brought by the owner and recorded at his instruction.
Its outside citations are its own and are attributed the same way. Its first line:

> **ADMIT-0 is the right first rung, but its first hardening should be parser unification, not merely a stricter
> JSON grammar.**

```text
proposal bytes ──► STRICT RECOGNIZER ──► typed proposal ──► ANCHOR CHECK ──► BOUNDED VERIFIER ──► DESIGN EVENT ──► SESSION
                        │ refuse                                │ stale: refuse
```

1. **One recognizer.** *Don't make three independent components parse the proposal language.* One admission parser
   turns the bytes into a typed proposal, and the verifier and the sealer receive that typed object and never the
   text. Three parsers that must agree is a permanent differential-parsing problem; one parser is one recognition
   boundary. Independent implementations stay as test oracles only.
2. **A language smaller than JSON.** Not "a JSON parser with a lot of security rules" but *a tiny world-design
   language with a formally bounded grammar*: an envelope and a bounded list of operations from a fixed vocabulary
   with bounded fields. The model's prose is metadata. The operation is what bears authority. The printable-ASCII,
   no-escape, no-leading-zero rules from the research are not locked as the architecture; the accepted representation
   of a purpose-built language is already canonical. JCS is not made the heart of it: *You control the admission
   language.*
3. **The anchor binds more than the head.** Program identity, renderer identity, session head and proposal schema.
   A proposal made against one head is never applied to another: no automatic rebase, no "close enough", no semantic
   merge hidden inside admission.
4. **Three identities.** `proposal_id` is this attempted admission. `proposal_digest` is these exact bytes. The
   session head is the authority it was proposed against. An admission record carries the id, the digest, the
   program and renderer identities, the parent head, the admitted event's digest and the resulting head.
5. **Typed refusals.** Not one "refused" but a reason: parse, size, depth, duplicate, unknown field, schema, range,
   anchor, program, capability, authority, duplicate proposal, I/O. A creator sees that an edit was not applied
   because the world moved while the model was writing it, and not that "AI failed".
6. **Proposal and admission are different objects.** The proposal is disposable. The design event is authoritative.
   Once admitted, the model's prose is irrelevant to authority.
7. **No filesystem capability for a model.** Not `write_file`, `execute`, `modify_source` or `shell`. A model gets
   `world.query` and `world.propose`, and perhaps later `world.preview` and `world.branch`. It describes a
   transformation, and only Verðandi turns one into an admitted event.
8. **The preview branch comes after admission works.** The order: `ADMIT-0`, then `DESIGN-EVENT-0`, then
   `LIVE-AI-EDIT-0`, then `BRANCH-0`. First prove prompt, proposal, admission, session, world, frame; then make that
   path disposable.
9. **Crash consistency belongs inside ADMIT-0.** After a death anywhere in an admission the session is exactly one
   of NOT ADMITTED or ADMITTED, never a half-state.
10. **Kill every boundary.** Proposal received, parsed, verified, anchor accepted, event materialized, event
    durable, session head durable, admission acknowledged. The process is terminated at each, and a restart finds
    the old head or the new head, never "I don't know".
11. **Capability bounds.** A proposal carries or inherits a scope: an authority, a region, a set of operations. An
    operation outside it is refused by the verifier however well formed it is. The enforcement sits below the model
    and is not a sentence in a prompt.
12. **Provenance attaches to the result.** An admitted event keeps its parent head, the proposal's digest, the
    intent text's digest, the proposer, the scope, the operation's digest, the resulting authority's digest, the
    renderer identity and a reference witness, so what changed, why, from which prompt and what the renderer showed
    are answered from the record and not from a model's memory.

**The courts the review registers with the rung.** They are part of ADMIT-0 and not rungs before it.

- **A. Reader court.** A hostile corpus: duplicate keys, unknown keys, trailing data, malformed UTF-8, invalid
  escapes, leading zeros, oversized numbers, excessive depth, oversized strings, an oversized proposal, truncated
  input, empty input, wrong types. Every one ends in a coded refusal and never in a panic.
- **B. Single-parser court.** The production parser produces the sole typed representation. Independent parsers
  are test oracles.
- **C. Anchor court.** The current head equals the proposal's parent head, or the proposal is refused. No rebase.
- **D. Capability court.** Operations outside the permitted vocabulary or scope all refuse.
- **E. Idempotency court.** The same proposal twice: the first is admitted, the second refused.
- **F. Crash court.** Termination at every admission boundary; recovery yields the old head or the new one.
- **G. Replay court.** The admitted event reproduces the exact resulting authority from the sealed parent.

The sentence the review locks:

> **The gate certifies the machine. ADMIT admits the world's changes.**

One correction the review makes to the research as pasted: `ReplaceFile` with its write-through flag is not to be
cited as the Windows durability mechanism, because Microsoft marks that flag unsupported. Checked here against
Microsoft's page: it does. The tree never calls `ReplaceFile`. Its replace is `MoveFileExW` with
`MOVEFILE_REPLACE_EXISTING | MOVEFILE_WRITE_THROUGH` (`shell/livesession.rs`), which is the primitive the review
names.

**The second court (2026-10-03), for the registration.** Held after the review, on the four questions it left
for the registration. The owner's rulings:

1. **The proposal language is a line language, locked for ADMIT-0.** In his words, *the proposal itself becomes a
   canonical byte artifact, rather than something that must be canonicalized after parsing.* The registration
   freezes the field vocabulary, the order, the line count, the separators and the integer domains. No optional
   lines, no arbitrary ordering, no nesting, no quoted strings, no escaping, no whitespace normalization, no
   Unicode, no duplicate fields (a field occurs once, at its registered position), nothing before the first line and
   nothing after the last, and LF (`0A`) the only line terminator. There is no parse, normalize, canonicalize and
   hash; there is recognize or refuse, and

   ```text
   proposal_digest = SHA256(exact proposal bytes)
   ```

   - **Not a world language.** *ADMIT-0 should admit the admission envelope*, with a small registered vocabulary
     for its operation, target and value. It does not try to encode the future landscape-edit language.
   - **Versions.** The first language is `VRDNP1`, frozen. A later one is a new version (`VRDNP2`) with
     deliberately different semantics, never a change to this one. That keeps the edit language from growing into
     an unbounded small programming language.
   - **The model writes the language and does not interpret it.** Natural language, then a line-language proposal,
     then admission, then a design event, then the world; never natural language, then arbitrary JSON or code,
     then an interpreter.
   - **Why not the others.** A strict JSON subset brings duplicate keys, escapes, Unicode, numbers, nesting and
     canonicalization back for no architectural gain. A binary record is a good storage form and the wrong proposal
     form: it puts an encoder between the model and admission, which is another trust boundary in front of the
     seam. Binary may still become an internal or session representation later.
   - **What the registration must fix.** *The exact ABNF-like grammar, allowed tokens, integer ranges, byte/line
     limits, and one worked canonical byte example.* Changing any of them afterwards is a new language version and
     not an implementation change.
   - **His sketch, recorded as a sketch.** `VRDNP1`, then `program=`, `renderer=`, `parent=`, `proposal=`,
     `scope=`, `op=`, `target=`, `value=`, one per line. It is "something along these lines"; the registration
     fixes the actual lines. Two things in it meet other rulings: its `program=` line meets ruling 4 below, which
     mints no program identity, and its example operation (`TERRAIN_RAISE` on `west_cliff`) is beyond today's
     vocabulary, which is a cell opened or closed and a tile class repainted.
2. **The saved-form reader is hardened in its own rung, after ADMIT-0: `READER-COURT-0`.** The two are different
   trust boundaries. ADMIT-0 establishes a new language and its recognition rules; the saved-form reader is old
   infrastructure with an observed disagreement surface, and joining them would make the first admission rung carry
   an unrelated migration. `READER-COURT-0` gives the shell's reader, the workshop's and the sealer's one coded
   verdict on the hostile corpus and closes the observed cases by name: trailing bytes and a second object,
   duplicate keys, malformed escapes, a `\u` cut short, a string ending at a backslash, excessive nesting and
   stack exhaustion, the disagreement on accepted numbers and strings, and the surrogate collision. No panic and no
   process abort. The affected reader files are re-pinned once, in that rung, and not dragged through ADMIT-0's
   development. *First we create the new admission seam; then we harden the legacy persistence seam it must
   coexist with.*
   - **The order he locks.** MOUSE-LOOK-0, the LLM-BUILDER-0 declaration, `ADMIT-0`, `READER-COURT-0`,
     `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0`, then branch and preview. This puts ADMIT-0 next after MOUSE-LOOK-0. Where
     the presentation and latency measurement, which the route above still lists, sits against this order was not
     ruled in this court.
3. **The admitter grants the scope.** The admit command takes the grant from whoever runs it. A proposal can only
   do less. The grant is recorded in the envelope, and the capability court tries to exceed it.
4. **The anchor's identity is what a session already records.** The renderer identity, the bearing identity, the
   session head and the proposal language's version. Nothing new is minted. A proposal goes stale when the head
   moves or the rendering sources change, and not when an unrelated file of the shell changes. The gate's rowset is
   not an anchor: it would tie content time to the gate.

**The third court (2026-10-03), on the frozen bytes.** The owner's sketch of the language had a `program=` line
and a `scope=` line, and the second court's rulings 3 and 4 took both away. Two rulings settled the lines.

1. **Eight lines, per the rulings.** `VRDNP1`, `renderer=`, `bearing=`, `parent=`, `proposal=`, `op=`, `target=`,
   `value=`. No program line, because nothing is minted. No scope line, because the grant is the admitter's and one
   operation per proposal leaves nothing narrower to ask for.
2. **The proposal id is the proposer's 64-hex handle.** Chosen by the proposer, carried in the bytes, untrusted and
   recorded. An id already in the session's admitted history is refused as a duplicate. The digest stays the SHA-256
   of the exact bytes.

**The registration (`bdd3859302f61b127c6df050cebf9ca521dc8bc2ca8a96e67b7f27150b39796d`).** Its own commit, with
nothing built. What it freezes, in `verify/preregister.json`:

- **The bytes.** Exactly eight lines, each ended by one LF, nothing before the first and nothing after the last.
  `renderer=`, `bearing=`, `parent=` and `proposal=` carry 64 lower-case hex characters. `op=` is `open`, `close` or
  `paint`. For open and close the target is `x,z` and the last line is exactly `value=0`; for paint the target is
  one of the five tile classes and the value is one integer, R×65536 + G×256 + B. Coordinates lie in 0..65535 and a
  colour in 0..16777215, with no leading zero. No other byte is legal. A proposal is therefore 327 to 337 bytes, each
  typed proposal has one byte sequence, and its digest is the SHA-256 of those bytes. The entry carries a worked
  example of 328 bytes and its digest.
- **What a proposal is checked against.** The renderer and bearing identities of the admitting shell; the head of
  the saved session as loaded (a stale parent refused, always, naming both heads); the ids already admitted in that
  session; the grant given on the command line; and the session's own validation of the edit, with one law added:
  a proposal that would leave W and M as they are is refused.
- **What an admitted proposal becomes.** The edit a key would make, with the head that edit gives. Its envelope
  (the language, the id, the digest, the two identities, the parent head, the resulting head, the grant) sits
  beside the event in the journal record and the saved item, travels with it through later continuations, and is
  never folded into the head.
- **Typed refusals, in a fixed order.** `ADMIT-IO`, `ADMIT-SIZE`, `ADMIT-PARSE`, `ADMIT-RANGE`, `ADMIT-PROGRAM`, the
  session loader's own, `ADMIT-SESSION`, `ADMIT-ANCHOR`, `ADMIT-DUPLICATE`, `ADMIT-CAPABILITY`, `ADMIT-AUTHORITY`. A
  refused admission leaves no run directory, no journal and no file.
- **The courts, as rows.** `admit-reader`, `admit-single`, `admit-anchor`, `admit-capability`, `admit-idempotent`,
  `admit-crash`, `admit-replay`, `admit-fence`, with `admit-preregistered` locking the entry.

Choices the registration makes beyond the rulings, each stated in the entry:

- One operation per proposal and one proposal per run. There is no batch.
- The review's parse, depth, duplicate-key, unknown-field and schema refusals are one refusal, `ADMIT-PARSE`, naming
  the line and what was expected. In a language with fixed positions and no nesting those cases are not distinct.
- Only a saved session can be admitted to. A crashed run's journal is refused `ADMIT-SESSION`.
- The proposal's bytes are not kept. The envelope is a record written by the admitting shell, and the seal is a
  hash and not a signature.
- The seam is per saved session. The same bytes offered to the child are refused as stale; admitted again to the
  untouched parent file, they make a second child with the same head.
- The crash court ends the process at eight points and shows process death, not power loss.
- `shell admit-anchor` prints the first four lines of a proposal for a saved session, and only reads.

**On the owner's host (2026-10-03).** The registration was applied and the gate run with the entry in the
registry: `GATE PASSED`, `RECONCILE  rowset a15345720a81009c  209 rows / 0 fail / 0 skipped`, the rowset and the
count it had before. The host's `verify/preregister.json` is byte-identical to the one registered here, 37 entries.
It was pushed as `0669ecf`. The registration reached the host before the docs commit that records the courts; the
two touch different files, and either order gives the same tree.

**The owner's acceptance (2026-10-03).** A review of the registration, brought by the owner and recorded at his
instruction. He accepts it as the ADMIT-0 design, with the distinction that it is a preregistered specification
and not an implementation result. In its words, the state is:

> **ADMIT-0: REGISTERED / BUILD PENDING.**

- **What the 209 rows show.** They are the gate as it stood plus the registration. They do not establish any of
  the entry's success conditions; the eight courts' rows do not exist yet.
- **The digest's limit, kept explicit.** The proposal's bytes are not kept, so the workshop and the sealer cannot
  recompute the digest in an envelope. The claim is that *the admitting shell measured and recorded the digest of
  the exact proposal bytes it received*. It is not that any later verifier can prove the recorded digest belongs to
  the original bytes. He would not add persistence of the proposal's bytes to remove the limit: that would enlarge
  the seam and bring the parser back into the downstream readers.
- **One operation, one proposal.** It gives atomicity without inventing batch semantics, and it leaves the crash
  court one possible new authority transition to interpret.
- **A boring vocabulary on purpose.** Open, close, paint. ADMIT-0 proves admission, not whether Verðandi can
  understand arbitrary landscape concepts.
- **The route is not changed, and the saved-form reader stays out.** MOUSE-LOOK-0, ADMIT-0, `READER-COURT-0`,
  `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0`, then branch and preview. The saved-form JSON disagreement is not pulled back
  into ADMIT-0.
- **What comes next.** *The next work is therefore implementation against the frozen 0105 bytes—not another
  design round.*

**Where the review meets what stands.** Read against the tree as it stood at the review. The courts above have
since ruled on these, and the registration settled the rest.

- **There is no proposal boundary yet.** The review speaks of the current proposal boundary having shown parser
  disagreement and crashes. What was observed is the saved-form reader, alone, on bytes no command was given. It is
  the reason to build the proposal's recognizer new and strict. It is not a defect found in an admission path,
  because none exists.
- **The gate.** The review's "PowerShell gate" is `verify/verify.py`, which the owner runs from PowerShell.
- **One recognizer, and the three verifiers of a saved session.** A saved session is verified today by three
  programs that each read the saved form: the shell, the workshop and the sealer. The review's rule is about the
  proposal language, and it holds only if nothing downstream ever needs the proposal's text again. So what is saved
  beside the admitted event is typed values the shell writes in its own saved form, and the digest of the
  proposal's bytes, which any verifier recomputes over bytes without parsing them. Embedding the proposal's text
  for the other verifiers to parse again, which was the draft before the review, is dropped. The three readers of
  the saved form remain, and their observed disagreement is closed in `READER-COURT-0`, after this rung (the second
  court, ruling 2).
- **The event ADMIT-0 admits.** By the court it is an ordinary session event in today's vocabulary: a cell edit or
  a tile edit, with the same head the same edit made by a key would give. A design-event kind of its own is
  `DESIGN-EVENT-0`'s business, not this rung's.
- **Scope.** A scope the proposal writes for itself bounds nothing. It bounds something when whoever admits grants
  it, and a proposal can only ask for less: ruled so (the second court, ruling 3). The world has no regions (see
  the section above), so today a scope can name operation kinds, cells and tile classes and nothing larger.
- **Identity.** The tree has a renderer identity (a digest over the render sources compiled into the shell) and a
  bearing identity, both recorded in a session's live block. It has no single program identity; the gate's rowset
  names a gate outcome, not a binary. Ruled (the second court, ruling 4): the anchor is what a session already
  records, and no program identity is minted.
- **`proposal_id`.** If the proposer chooses it, it is as untrusted as the rest of the proposal. Refuse-always
  already makes a second admission of the same bytes stale. Ruled (the third court, ruling 2): the id is the
  proposer's handle, and a duplicate refusal compares it with the ids already admitted in the session.
- **What a crash court can show.** Terminating the process shows what a restart finds after the process dies. It
  does not show a power loss: bytes written and not flushed survive a killed process in the system's cache.
  Microsoft's page promises the write-through flush for a move performed as a copy and delete and is silent on
  atomicity. The court's claim is worded as process death; durability under power loss stays DECLARED from the
  platform's documentation and NOT_MEASURED.
- **The names after ADMIT-0.** `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0` and `BRANCH-0` are the review's order. Each is
  still chosen in its own court. The four rules at the end of the section above stand: commit-only meets
  `BRANCH-0`, and earn-the-authority meets every example the review uses (cliffs, a valley, terrain, materials,
  populations), none of which the frozen oracle certifies.
- **Refusal codes.** The review's list gives the reasons. The registration gives them codes in the tree's form and
  says that a refused admission writes nothing to the session and is recorded like any other refusal.

**Grade.** DECLARED: the three courts' rulings, the review and its seven courts, the registration's conditions,
the owner's acceptance. MEASURED (on the host): the gate passes with the entry in the registry, 209 rows, the rowset
unchanged. OBSERVED: the 19-input table, here, outside the gate. Attributed and not claimed: everything under "What
the research found". Nothing about the seam itself is ESTABLISHED or MEASURED. **does_not_show.** That a strict
recognizer exists; that any of the courts holds; that a model can write a proposal worth admitting; any safety
property of a system that includes a model. The state is registered, build pending.

### The design language — one design authority, many editors · **declared** (the owner's, 2026-10-03); not registered, nothing built
A design text the owner brought on 2026-10-03, after the registration, and asked to have recorded. Like the two
texts above it is a reply to his own description of what he is after, so its wording is quoted where it states the
rule and summarized elsewhere. It extends the design-event stream and seats nothing.

> **Intent → constrained design operation → verified state transition → provenance → deterministic projection.**

- **The design environment is itself a typed, deterministic, inspectable program.** In the text's phrase, *a CAD
  for interactive worlds*, where every design operation has the properties the admission seam is establishing.
- **Design objects and constraints, not tools.** The environment is not built around a wall tool, a terrain tool
  and a mesh tool. It is built around a design state with five parts: geometry (surfaces, volumes, boundaries,
  transforms), semantics (rooms, paths, cover, spawn zones, gameplay volumes, tags), relations (adjacent to,
  contains, connects, blocks, visible from), constraints (dimensions, reachability, clearance, performance,
  visibility, gameplay invariants) and provenance (author, operation, parent, constraint result, resulting
  identity). A viewport is one projection of that state.
- **Geometry is not the primitive.** Conventional CAD goes point, line, surface, solid. Here the order is *intent →
  relation → constraint → realization*. A request is turned into a bounded design representation, and the system
  asks whether the intent can be represented, whether its constraints can coexist, what authority it touches, what
  changed and which constraints became invalid. The answer is a design diff.
- **Constraints are first-class world objects.** Persistent objects with a kind, a subject, a value, a status and a
  witness, and not validation code alone. A design change then has a consequence graph: the operation, the objects
  it changed, the constraints it affected, each satisfied, violated or unknown. What that gives, in the text's
  words: *a machine-readable explanation of why a world is still valid.*
- **One authority, many projections.** The same object seen as geometry (walls, doors, materials), as gameplay
  (cover, routes, spawns) and as runtime cost (draw cost, memory, streaming), with no editor copy of the object
  beside a runtime copy. The text names five such environments over one authority: spatial, gameplay, simulation,
  narrative and performance.
- **A model gets a design language and nothing else.** A proposal goes through a compiler to a candidate diff, the
  constraints are evaluated, a human sees a preview, and only then is it admitted. The model never writes
  arbitrary files, executes arbitrary code or mutates authority. The renderer stays downstream, the model is not an
  authority, and the interface is not the source of truth.
- **Reversible design, as provenance.** Every object keeps its lineage: the event that created it, the events that
  changed it, the constraints on it, the projection that shows it. "Why is this wall here?" is answered from that
  record. The text calls it design provenance and not merely undo history.
- **What the text would not do, and the rung it proposes instead.** It would not start *a giant "next-gen CAD
  editor"*. It proposes a small rung, `DESIGN-IR-0`, proving only a typed design object, a typed relation, a typed
  constraint, a bounded diff, a deterministic serialization and provenance: no viewport, no model, no mesh editor,
  no giant schema. Its one vertical slice is *a rectangular room with doors, connectivity, clearance, and a gameplay
  tag*, produced identically by a human-authored operation and by a hypothetical model's proposal, then mutated on
  purpose to show the constraint's witness change deterministically.

Its last lines:

> **Don't build an AI level editor. Build a deterministic design language with many editors.**

and: the thing that survives every editor is *the design authority + constraints + provenance*.

**What already stands that it would rest on.** The admission seam is registered, with a vocabulary that is boring
on purpose. A projection that never writes is the existing separation of workshop, kernel and shell, and the
invariants below already forbid a view from holding authority. WORKSHOP-0 refuses a record whose projection is
stale under a moved authority, which is one derived thing already tied to the authority it was derived from.
SEMANTIC-0, above, is the named and unbuilt rung for meaning beyond what the oracle certifies. The HUD's pins are
the one case so far of VIEW semantics earned here and held by rows.

**What does not exist.** A design object of any kind. Rooms, doors as objects, paths, cover, spawn zones, volumes
or tags. A relation. A constraint, a constraint's witness, or a solver. A compiler from intent to operations. A
second projection of the world beside the frame and the HUD. Units: the world is a grid of cells and five tile
classes, with no metre, no second and no height.

**Where it meets rules already in force.** Each of these wants the owner's ruling before a rung is seated.

- **Earn the authority.** Anything that decides W or M is CORE and comes only from Urðr, carried or earned there
  and re-frozen. A layer that only names and reads what W already holds (a room as a set of cells, reachability as
  a path over open cells) could instead be VIEW semantics by SEMANTIC-0's route: a reference here, pinned by rows,
  never writing the world. Which route each kind of object takes is a ruling, object kind by object kind.
- **A constraint's status is a witness, not a field.** The declaration of a constraint is authored content, and if
  it is admitted it is an event. Its status is derived from the world. A saved `status = SATISFIED` that a reader
  trusts is a second authority. In this tree the equivalent of a status is a witness: recomputed by replay, compared
  and refused when it differs, never taken from the file.
- **Float-free, and in the world's own units.** The examples speak in metres, seconds and percentages. The rules
  here are integers of the world: cells, ticks, reduced rationals.
- **A panel, not a score.** "14 satisfied, 1 degraded, 0 violated" is a count per status and is admissible as
  that. It is not folded into one number, and "degraded" needs a definition before it is a status.
- **Preview before admission.** The text's flow shows a human preview before the admit. Commit-only still holds: a
  preview is a speculative worldline, a typed log replayed from an anchored head, and that is the branch rung's
  business, after admission works.
- **The compiler.** If it is code in this tree it is program and the gate certifies it. If it is a model it is
  outside the tree. Either way its output is a proposal in a registered language, and the seam admits or refuses it.
- **The order.** The owner's locked order is ADMIT-0, `READER-COURT-0`, `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0`, then
  branch and preview, and his acceptance of the registration says the next work is implementation and not another
  design round. Where `DESIGN-IR-0` sits against `DESIGN-EVENT-0` was not ruled. It is recorded here as a declared
  name and is not seated.

**Grade.** DECLARED: all of it. Nothing here is established or measured. **does_not_show.** That a design object,
a relation or a constraint can be defined over this world without new CORE semantics; that a constraint's witness
can be computed deterministically for anything beyond what the grid already says; that a model can write in such a
language. When a rung is seated from it, the rung registers its own hypothesis, failure condition and limits.


### READER-COURT-0 — the saved form's readers brought to one verdict · **built** (`f53017cd`): the gate passes here; the first host run read 225 of 226 and the one red is fixed; the second host run passes and is pushed
The rung after ADMIT-0, by the owner's order. ADMIT-0 made a new language with one reader. This rung hardens the old
one: the JSON the tree saves and reads back. The disagreement it closes was observed on 2026-10-03 and is recorded in
ADMIT-0's section above. This section records what was read from the code before the courts, the two courts, a
review the owner asked for, the registration and the owner's review of it, and then the build.

**What was read from the code, before the courts.**

- **Four Rust parsers, not three.** One text is copied byte for byte into `shell/playback.rs`,
  `workshop/sessionwalk.rs` and `workshop/session.rs`. `workshop/edit.rs` has a fourth parser, a different text,
  for edit records.
- **Four Python readers.** `verify/livesession.py` (the sealer), `verify/seal_sessionwalk.py`,
  `verify/seal_session.py` and `verify/envelope.py`'s `read` each read saved-form documents with `json.load`.
- **Three writers, three layouts.** The shell writes a saved session, a journal's record payloads and a checkpoint's
  one line by format strings. The workshop writes an indented document from a parsed value. Python writes a sealed
  record with `json.dump`, indented, not escaping non-ASCII, with one LF after it.
- **The corpus is inside a small language.** The 24 session-walk files the Rust readers can meet (committed
  records, the host's sealed records, the host's saved sessions) hold no escape, no fraction, no exponent and no
  duplicate name; 14 hold raw UTF-8. Across all 39 record files of every kind there is no fraction or exponent, and
  the only escapes are `\"` and `\\`. The deepest shape is 7 levels: sixteen of the host's sealed measurement
  records (FRAME-SPLIT-0's is root, data, arms, production, split, phases_us, strips). *Corrected on 2026-10-04:
  this line first said 6 levels, a sealed WORKSHOP-1 session record (root, data, log, item, edit, rgb). That is the
  deepest among the session files; the count had missed the measurement records. The recount was made while the
  registration was drafted, which is why the entry says seven.*
- **The writers disagree on two characters.** The shell and Python write backspace and form feed as `\b` and
  `\f`. The workshop writes `\u0008` and `\u000c`. The Rust reader refuses `\b` and `\f`, which the shell's own
  writer can emit. No file has ever held either character.
- **The integer bound is the reader's.** The shell holds ticks and counts as unsigned 64-bit and writes them
  unchecked. The reader takes signed 64-bit. Only the shell's read-back after a save enforces it.

**The first court (2026-10-04).** Four rulings.

1. **The writers' language. LOCK.** Strict RFC 8259 is rejected: it would make the reader's language larger than
   the saved-form authority and force a float on a system whose rules are integers. Canonical bytes are rejected:
   the three writers share a data language, not one serialization. The owner's refinement of the ruling:

   > **The accepted language is the bounded saved-form language that the tree's registered writers are permitted
   > to emit.**

   - *Corpus establishes coverage; the writer contract establishes the language.* The 24 files show the existing
     corpus lies inside it. The court tests its boundary: a writer-valid integer and a float, a writer-valid escape
     and another, valid and invalid UTF-8, the deepest nesting and one deeper, the final LF and a byte after it, a
     unique name and a repeated one.
   - **Bounds come from the writers, not from the files.** Depth is not 6 because the files stop at 6: the writer is
     asked what it can emit. If a writer has no explicit bound, that is the seam to close before the grammar is
     locked. The same for 64 bits: a semantic invariant, or an artifact of one parser.
   - *The saved-form reader is not a general JSON reader. It is a reader for Verðandi's own persisted language.*
2. **One file, shared by path. LOCK.** The copies are evidence that extraction is safe, not a reason to keep
   them. *One persisted language → one reader → many consumers.* The shared module owns saved-form parsing and
   decoding only. It knows nothing of the shell, the workshop's editing, admission, the renderer, session
   mutation, authority or any interface. The rung pins the language and the reader's behaviour, not that the files
   compile.
3. **The sealer gets its own strict reader, held by the court. LOCK.** Two implementations at the verification
   boundary are wanted, not tolerated: a sealer that deferred to the Rust reader would turn the observed
   disagreement into a dependency nobody can see. `json.loads` is rejected as an authority on either side: the
   Python reader implements the locked language itself, with no `json.loads` underneath as a fallback. Neither
   reader is right because the other agrees. *Agreement demonstrates consistency; it does not by itself prove
   correctness.* The end state: *one production implementation, two independent implementations at the
   verification boundary.*
4. **A hostile file gets the same code and the same byte offset from every reader.**

**The review the owner asked for, of ruling 3.** Agreed, with what it obliges.

- **The Python reader is production for the sealer.** With no `json.loads` underneath, the sealer reads a saved
  session with the strict reader. The sealer also runs the workshop's verify on the same file, so a file is sealed
  only if both readers accept it.
- **Agreement cannot catch a mistake in the specification.** Both readers are written by one author from one
  grammar. What stands against that: boundary cases with their expected verdicts written into the registration, and
  the writers as a third witness, every writer's output required to be accepted.
- **"The same typed value" needs one rendering both compute.** A digest of a canonical dump: names in byte order,
  no whitespace, one escape spelling.
- **"The same byte offset" needs a definition neither implementation owns.** The first byte at which the input
  stops being a prefix of any document of the language, or its length if it is cut short. For a repeated name that
  is its closing quote; for an integer, the digit that takes it out of range. Both readers validate UTF-8 by hand, so
  that they stop at the same byte.
- **Exhaustive mutation of real files is not affordable in Python.** The host's 376 KB session has about 190
  million single-byte mutants.
- **The gate's older rows read saved files with `json.loads`.** That is test code inspecting what the shell wrote.
  They are left as they are, and this rung's rows use the court reader only.

**The second court (2026-10-04).** Four rulings on what the code had turned up.

1. **Every reader of the saved form.** All four Rust parsers become the one shared reader, `workshop/edit.rs`
   included. Every Python tool that reads a saved-form document reads it through the court reader.
2. **One spelling.** The two-character escapes where they exist (`\"`, `\\`, `\b`, `\f`, `\n`, `\r`, `\t`) and
   `\u00XX` in lower-case hex for the other control characters only. The workshop's writer is aligned to it. Every
   string then has one byte form.
3. **Signed 64-bit is the law, and writers refuse beyond it.** An integer lies in -2^63 to 2^63-1, with no leading
   zero and no minus zero. A writer refuses to write a value outside it, so the bound is the format's and not one
   parser's. The court tests both edges.
4. **Exhaustive on small documents, boundary mutations on real files.** Every single-byte mutant of a few small
   registered documents that between them use every construct of the language. On each real file: acceptance, the
   same typed value in both readers, and the registered boundary mutations at every place they fit.

**Grade.** DECLARED: the two courts' eight rulings. OBSERVED: what was read from the code and counted in the files,
here, outside the gate. **does_not_show.** That a shared reader exists; that the two readers agree on anything; that
the writers' contract has been derived writer by writer. The registration does that derivation and fixes the
grammar and its bounds before a line is built.

**The registration (`f53017cd`).** The entry fixes the language, the verdict, the readers, the writers and the court
before anything is built. Its terms are in [`verify/RUNGS.md`](../verify/RUNGS.md); in short:

- **The language.** A document is one object and exactly one line feed. Between tokens, spaces and line feeds only.
  No name twice in an object. Integers in signed 64 bits with no leading zero, no minus zero, no fraction and no
  exponent. Strings in well-formed UTF-8 with one spelling. At most seven levels of objects and arrays, counting
  those open at once with the root object as the first.
- **The verdict.** Accepted with a typed value, or refused with one of seven codes and the offset of the first byte
  at which the input stops being the beginning of any document. The offset belongs to the language, not to a reader.
- **The court.** 45 boundary cases with their verdicts written into the entry; every single-byte substitution,
  deletion and insertion of three small registered documents; the registered boundary mutations on every real file.
- **The limits.** Both readers have one author; the exhaustive court covers three small documents; the raws, the
  two logs, the registry and the frozen JSON under `oracle/` are not the saved form and are not covered.

**The owner's review of the registration (2026-10-04), before it was pushed.** The entry was first drafted with hash
`0ecbec22`, applied on the owner's host and gated there, and not pushed. His review locked it point by point: the
depth of seven, provided the counting convention is explicit; the writers checking their own bytes, with the
format's definition standing above both the reader and the writers; the reader in `kernel/` as a shared file that
is no part of the renderer's identity; one string spelling; spaces and line feeds as the only whitespace; the first
and the last place of each kind for large files; the raws, the logs and the registry left out; and ADMIT-0's pin of
the old reader's text moving here (*historical pin ≠ current implementation*, and history is not rewritten). He
asked that the prototype's result stay labelled a compatibility measurement taken outside the gate, and not be read
as equivalence with Python. And he set one condition for the push: the depth convention explicit, and the court
showing six levels accepted, seven accepted and eight refused at the exact offset. The convention and the seven and
eight cases were in the draft. The six was not. The entry was amended while its commit was still unpushed, as the
rules allow, and its hash is now `f53017cd`. *0110: LOCK / PUSH. No redesign.*

**On the host (DANIELDILLBERG).** The unpushed draft was dropped (`git reset --hard f504829`), the registration and
the documents were applied, and the gate passed there: GATE PASSED, rowset `0b423b279a40c85c`, 218 rows, 0 fail, 0
skipped, the same as here. Pushed, `f504829..25b5c17`. The entry is public; from here it changes only by an
amendment with its own hash.

**The build.** On the owner's word, *take the next*. One Rust reader, `kernel/savedform.rs`, replaces the four
parsers (about 840 lines removed) and is included by path by the shell and the workshop's three tools. An
independent Python reader, `verify/savedform.py`, replaces `json.load` in the four Python tools. Every writer gives
its bytes to the reader before it writes them. Eight rows, 226 in the gate (rowset `39e5874a7127cfa4`): the 45
registered cases; 163,072 single-byte mutants of the three registered documents with the same verdict from both
readers on every one; 43,925 boundary mutations of the committed records and of what the gate makes (181,376 with
the host's 33 records present), each with the code and offset its place gives; the writers; a hostile document
refused by seven real commands with the same code and offset; one reader by source; and the fence. Nine earlier
rows' forgeries were rewritten inside the language, and one pin moved, both listed in the ledger. 55 planted
defects are each caught. The details, the limits and the falsifier are in
[`verify/RUNGS.md`](../verify/RUNGS.md).

**The first host run.** 226 rows, one red: `readercourt-fence`, naming `shell-playback-sealed-input`. That row's
planted file had been opened in text mode, so on Windows it ended in CR LF, which the language refuses before the
row's own rule is reached. The row stayed green; the watch this rung added went red. The plant is now written as
bytes. Every other row passed on the host, the corpus with the host's records among them.

**The second host run (2026-10-05).** With the fix and its record applied the gate read `GATE PASSED`, rowset
`39e5874a7127cfa4`, 226 rows / 0 fail / 0 skipped, and the owner pushed `b847810..b077eef`. READER-COURT-0 is
landed on both machines.

**The next question, reserved.** The owner asked whether DESIGN-EVENT-0 remains the next rung after this one, or
whether a design representation, a design diff and constraints are promoted ahead of it, as the review of the
development environment below would have it. His words: *I would not silently reorder that based on the 15-pivot
review. That deserves its own ruling.* Nothing is reordered here. The locked order stands until he rules.

*Ruled on 2026-10-06: DESIGN-EVENT-0 stays next, and the design representation follows it. See DESIGN-EVENT-0 below.*

### The development environment — fifteen pivots · **declared** (the owner's, 2026-10-04); not registered, nothing built
A review the owner brought on 2026-10-04 and asked to have recorded: Verðandi judged as a research-grade interactive
development environment and not as a game editor. Like the texts above it is a reply to his own description, so its
wording is quoted where it states a rule and summarized elsewhere. Its citations of the ACM literature are its own
and were not opened here; they are attributed, not claimed. It seats nothing. Its verdict is its own too: a very
high architectural score with fifteen product pivots. This repository keeps no scalar scorecard, and the verdict is
recorded as the review's.

**The risk it names.** *A beautifully rigorous engine with an underdeveloped development environment.* What it
finds already strong is the path from intent to a typed bounded proposal, admission, session, authority and a
deterministic projection, and the property that follows:

> **The visual editor does not become the source of truth.**

**The fifteen pivots.**

1. **A design space as a first-class window.** A workspace over authority (world, scene, selection, tools,
   constraints, layers, views, panels, bookmarks), several open at once, none a copy of the world.
2. **A docking and window system, early.** Scene, viewport, inspector, and a bottom band for the timeline, the
   session, diagnostics, a console and admissions. Every pane is *a projection of authority, never authority
   itself*. Layouts are saved by role.
3. **View modes, not only camera modes.** The same world as perspective, top, side, orthographic, wireframe,
   collision, navigation, visibility, lighting, gameplay, network, streaming, performance. The geometry does not
   change; the projection does.
4. **Constraints as a visible subsystem.** A constraint with an id, a type, a subject, parameters, a status, a
   witness and provenance, listed in the interface, a failure highlighting the geometry it is about. Verification as
   design instrumentation and not a terminal event.
5. **A design diff window.** What changed spatially, which semantic objects, which constraints, which performance
   consequences, which provenance; then accept, reject, inspect, revert or branch.
6. **A parameter rack.** An object's parameters as design intent: changing one generates a typed operation, so it
   stays editable, undoable, replayable, provenance-bearing and addressable by a model.
7. **Design recipes.** A parameterized design procedure and not a prefab. It produces a proposal and never mutates
   authority. A model manipulates recipes instead of inventing geometry.
8. **Preview unmistakably not the world.** The current world solid, the proposed one ghosted, with its counts and
   its constraints, manipulable before it is admitted. Feedback at the design boundary and not everywhere.
9. **A command palette over the whole architecture.** Every command resolves to a typed operation. It is another
   frontend and not a second interface to the world.
10. **Portable project bundles.** A manifest, the authority, sessions, the design representation, constraints,
    provenance, assets, the renderer identity and compatibility metadata; opened on another machine by verifying,
    reporting differences, then opening.
11. **A compatibility inspector.** Each format and identity reported on opening, with open, open read-only, repair
    and export as choices. *Never silently migrate authority.*
12. **A capability and tool permission system.** ADMIT-0's grant grown into a platform primitive: a tool or a model
    is given `world.query` and `world.propose` and not filesystem writes, process execution or authority mutation.
13. **A plugin SDK around projections, not authority.** Read the model, analyze, propose, court, admit. A plugin
    says "I propose these changes" and never "I modified the world".
14. **Multi-representation editing.** The same object edited by dragging, by a number, by text and by a structured
    form, all four compiling to the same design operation.
15. **The design observatory.** A persistent window of the design's state: objects, constraints, violations and
    unknowns; performance; gameplay; provenance; admission. Not another debugger. It answers *why does the system
    believe this world is valid?*

**Its order.** Five layers. A, the foundation: the shared reader and READER-COURT-0, then a design representation,
the design diff, constraint objects. B, a real editor: docking windows, view modes, the parameter rack, the command
palette. C, authoring: recipes, the proposal and preview workspace, multi-representation editing. D, the platform:
capabilities, the plugin SDK, project bundles and the compatibility inspector. E, the differentiator: the
observatory. If only three, it picks the design representation with constraints as first-class objects,
multi-representation editing, and the observatory.

**What it would not copy.** Not an existing engine's editor made deterministic, not a modelling tool for games, not
an engine with a model attached. Its proposition:

> **Verðandi is a design environment in which visual manipulation, text, AI proposals, procedural tools, simulation,
> and verification are all different frontends to the same typed, provenance-bearing design authority.**

**What already stands that it would rest on.**

- **Two frontends already compile to one operation.** ADMIT-0's replay row holds that a proposal and a key give the
  same event, the same witness and the same head. That is multi-representation editing for the two representations
  the tree has.
- **The grant is the first capability.** ADMIT-0 takes its scope from whoever runs it, and a proposal cannot widen
  it.
- **Opening a session already reports and never migrates.** The loader classifies a saved session as loading, as
  loading under a different renderer, as tampered or as made by a different renderer, and refuses what it cannot
  replay. The shared reader this rung is about gives the saved form a language that can be named.
- **Some diagnostics already exist as text.** The refusal log and the run ledger, with their readers, are what an
  admissions or diagnostics pane would show.
- **A projection that never writes** is the existing separation of kernel, workshop and shell, and the invariants
  below.

**What does not exist.** Any window but one borderless picture and its overlay. A pane, a dock, a menu, a layout, a
selection, a palette. A design space. A second view mode. A constraint, a recipe, a parameter of an object, or an
object. A project bundle or a manifest. A plugin. Anything the observatory would count beyond events, refusals and
runs.

**Where it meets rules already in force.** Each wants the owner's ruling before a rung is seated.

- **Floats, units and scores.** The examples use metres, fractions and a cover score of 0.71. The world's rules
  are integers of the world, and a score is not kept: a panel of counts per status is.
- **A constraint's status is a witness.** As recorded with the design language above: recomputed and compared,
  never a saved field that a reader trusts.
- **Numbers shown are measurements.** A frame time or a memory figure in an observatory is a claim, and a claim
  here has a registered instrument behind it or is not made.
- **Preview.** A proposed world that the user manipulates before admitting is state. Commit-only holds: it is a
  speculative worldline, a typed log replayed from an anchored head, or it is a second authority in the shell.
- **Recipes and batches.** A recipe yields many operations. VRDNP1 carries one, and ADMIT-0 registered that there
  is no batch. A batch is a new language version with its own atomicity court.
- **Plugins and the gate.** The gate certifies the program, and no path executes text. A plugin that runs inside
  the program at content time is code the gate did not certify. A plugin that runs outside and hands over a
  proposal is a proposer like any other.
- **A window system.** The shell is hand-written Win32 with no dependency, and its presenter is held to showing the
  certified picture exactly, read back from the screen. Docking, panes and menus are a large addition to that
  surface, and every pane is a VIEW or an OBSERVER: with all of them open, replay stays byte-identical.
- **The order.** The owner's locked order after READER-COURT-0 is `DESIGN-EVENT-0`, `LIVE-AI-EDIT-0`, then branch
  and preview. This review's layer A puts a design representation, the design diff and constraint objects there
  and does not name the other two. Which order stands was not ruled. READER-COURT-0 is first in both.

**Grade.** DECLARED: all of it. Nothing here is established or measured. **does_not_show.** That any pane, view
mode, constraint, recipe, bundle or plugin can be built under the rules above; that the fifteen are the right
fifteen; anything about how a user would fare with them. Each rung seated from it registers its own hypothesis,
failure condition and limits.

### REASON-COURT-0 — every refusal held to its reason · **built** (`337ab021`): six rows, 232 in the gate; the gate passes here and on the host; pushed
The rung after READER-COURT-0, by the owner's ruling. Its census is taken, three courts are held, and the method is
registered with its register, `verify/reasons.json`. Nothing is built. The full record is in
[`verify/RUNGS.md`](../verify/RUNGS.md); this section keeps the order of events.

**Where it came from.** READER-COURT-0 made the gate watch every refusal by the saved form's reader. The watch
showed a row, `shell-playback-sealed-input`, that had stayed green while its planted file was refused for its form
and not for being what the row says it is. A row that asks only for a refusal passes whatever refused. That gap is
not the reader's: READER-COURT-0 holds its own refusals to an exact code and a byte offset. It is in the rows of
the rungs before it.

**The owner's ruling on the idea.** *LOCK the idea, REGISTER the court.* A reason-code court, not a general proof of
diagnostics. For each refusal row: the input, the expected verdict, the expected reason code, the observed verdict,
the observed reason code; an acceptance must equal an acceptance, and a refusal's observed code must equal the
expected one. Where the precise reason is intentionally unspecified the row keeps `REFUSE(any)`, because otherwise
an incidental ordering inside the implementation is frozen as authority. Four things are told apart:

| | |
|---|---|
| a semantic refusal code | locked contract |
| an implementation's diagnostic text | not locked |
| a byte offset | locked where a rung already specified it |
| an internal exception, stack or branch | never authority |

The most valuable cases are the same input failing for a different cause. Where a malformed input could fail at
either of two boundaries, the registration says which boundary owns the failure; otherwise the court turns today's
branch order into tomorrow's contract. And the expected reasons are registered before results are observed, so
they are not fitted to what a program happens to emit.

**The court (2026-10-04).** Three rulings.

1. **Its own rung, REASON-COURT-0.** READER-COURT-0 is not amended. The red row on the host was a defect in
   READER-COURT-0's build (a planted file written CR LF on Windows), and the reader's verdict on it was the correct
   one; it is no evidence that the reader court's reason contract is wrong. The ladder as the owner wrote it:
   ADMIT-0, READER-COURT-0, REASON-COURT-0, DESIGN-EVENT-0.
2. **Every refusal check in the gate.** A court that covered only the codes already named would keep the blind spot
   and not measure it. Each check is classed as an exact code or as `REFUSE(any)`. *`REFUSE(any)` is not a failure to
   specify*: it is a registered decision that the court does not constrain that row's reason, with why. A check that
   rests on a fragment of text or on the exit status alone is classed as that and is not silently promoted. A row
   is not made exact merely because its reason can be named. Once a reason is promoted to an exact code, a later
   change to it needs an explicit decision.
3. **The expected code comes from the rung's registered text or its ledger entry.** Where neither names one, the
   row is `REFUSE(any)` and is listed. Never from what the program emits today.

**The census comes first, and it changes nothing.** The owner's boundary: old rows are not strengthened during the
census. It records, for every refusal assertion in the gate, the row, the evidence it rests on and the strength of
the assertion as it stands (an exact code, a fragment of text, the exit status alone, other evidence), and the
rung whose text owns the reason. Only then is what REASON-COURT-0 will strengthen preregistered. Otherwise the
census would be a way to rewrite history quietly.

**What was counted so far (OBSERVED, crude, not the census).** A pattern search over the gate found about fifty
checks of an exit status of 2. About half name a code. Three match a word of diagnostic text (`"alphabet"`,
`"width"`, `"border"`), which a message could contain by accident. About ten rest on the exit status beside other
evidence, such as a count of log records or a file that must not exist. The owner's note: do not assume that
figure is the population.

**What the first text left open, and how the court settled it.** It said both to register the court separately and
to add it to READER-COURT-0 as a sub-court built with the reader. READER-COURT-0's entry was already pushed and
its build delivered, so the second was no longer available as written; the court chose the first.

**The census (2026-10-05), which replaced the crude count.** The gate as patch 0116 left it was read line by line
in twelve windows, extracted a second time from its syntax tree, and netted a third time over its own failure
texts. It changed nothing. 190 statements; 145 refusal checks in 78 of the 226 rows; 16 second witnesses; 4 planted
deaths; and, apart, 7 detections, 6 of the gate's own checks, 1 agreement court and 63 places that trust a
program's own court. Of the 145: 103 hold a code, 8 hold words, 12 hold other evidence, 22 hold only that the
subject refused, and 21 of those 22 are the sealers, which refuse in prose. Of the codes, a ledger entry named 23
and `RUNGS.md` 15; 45 were named only by the program that prints them and the row that asks for them. The crude
count had said about fifty checks; the population was three times that.

**A listening pass, off the gate.** One run of the whole gate with a listener on: 1,103 children ended non-zero and
74 sealer refusals were raised, with no panic, a code on every refusal of this tree's programs, and every sealer
refusal for the cause its row names. No wrong-reason pass was found among what it could hear. It is evidence about
one run and never the source of an expected value.

**The second court (2026-10-05): four rulings.**

1. **The edge: refusals and deaths.** The 145, their 16 second witnesses and the 4 planted deaths are held. The
   detections, the gate-self checks, the agreement court and the programs' own courts are registered as outside.
2. **Register the codes here, each with a witness.** A requirement that already exists may be registered; a new one
   may not be manufactured; the implementation establishes no expected code. `RUNGS.md`'s state is pinned.
3. **The sealers: `REFUSE(any)` with a condition.** No sealer is given a code and none is changed.
4. **A table and a watch.** The table is the authority; the watch claims every child that does not end 0; the old
   statements are not rewritten.

**The third court (2026-10-05): two tightenings.** The two rulings met at one point: the watch was to read "the
boundary prefix and the full code as the first token", and the prefix is in no row and no registered text. The
owner corrected his own wording: the watch reads the **code head**, the leading run of code tokens on a line; the
prefix is observed framing and is not registered; the few codes that stand in prose are named exceptions. And the
sealer condition is **one registered mutation with its recomputation closure**: 41 of 57 planted records meet it,
and the 16 that do not are registered as debt, `NOT_MET`, owed a code or an accepted twin.

**Registered (2026-10-05).** Entry `337ab021`. The register holds 83 codes with their sources, 165 statements with
the gate's own text that requires each, 1,103 endings in 77 groups, the planted records beside their twins, and
the statements outside the court. Four numbers moved between the court and the registration, each by the owner's
own test, and are listed in `verify/RUNGS.md`. Six rows are registered for the build.

**Pushed (2026-10-05).** On the host the gate read `GATE PASSED`, 226 rows / 0 fail, with the entry and the
register in the tree, and the owner pushed `b077eef..c057da2`. The entry and the register are fixed from there.

**The fourth court (2026-10-05): three rulings, after a review and two texts the owner brought.**

1. **A loose name in the register's counts is held in the build, not amended.** One count,
   `endings_with_one_code_in_prose: 3`, reads as a fifth part of a partition that has four. The entry's own
   sentence gives the four (1,072 + 23 + 6 + 2 = 1,103), and the three sit inside the 1,072. The build's register
   row asserts that, is planted with the misreading, and cites the entry's sentence as its witness.
2. **The host is heard before the build.** The gate takes no input, so its endings depend on the platform and the
   records present: three configurations, not endless runs. Two were heard here with one instrument kept outside
   the repository, on two interpreters; in all three passes the 1,103 endings were heard and all 77 groups held.
   The third is the host, with the same instrument byte for byte. A difference is a finding settled by amendment.
3. **The in-process gap is lived with and measured; nothing is seated.** The watch cannot see a refusal judged
   inside the gate's own process. The same instrument counted them at the place they are raised, from the
   interpreter's own events and touching nothing: 142,083 refusal-type exceptions in 16 rows (74 the sealers', 32
   the envelope's, the rest the Python reader's), every one but one claimed by a registered statement or by the
   agreement court.

**Declared in that court, each for a court of its own; neither is on the ladder.**

- **An accounting of refusal sites.** Every comparison of an exit status and every handler of a refusal exception
  in the gate is a registered statement or a named non-refusal. Decidable, because it claims and does not classify.
  It does not see a refusal judged by another shape.
- **A refusal as an emission, for the gate's own process.** The sealers would return a verdict where they raise, as
  the readers return a verdict line and the children write a refusal record. It changes the sealers' interface,
  so it is a rung of its own; its census is the count above.

A formal semantics of the watch, proposed in one of the texts, is recorded as declared and is not on the route.

**Heard on the host (2026-10-05).** 0119 was applied and pushed there (`c057da2..f145a8d`). The owner ran the
listen-only pass with the same instrument, byte for byte, on win32 under Python 3.14.5: the gate inside it passed
(226 rows, 0 failed); 1,103 endings heard and 1,103 registered; 77 of 77 groups holding; nothing outside the
watch's scope; no finding. The fourth configuration reads as the three here did.

**The fifth court (2026-10-05): the in-process gap becomes a slice of its own.** The owner took the count of mints
as a real slice with a narrower claim than a reason court, and registered it separately as MINT-WATCH-0 (below).
REASON-COURT-0 is not amended. Requiring an exception to carry a code stays deferred.

**Built (2026-10-05).** One file changes, `verify/verify.py`; the entry, both registers, every program and every
sealer are as they were. The watch READER-COURT-0 put on `subprocess.run` now also keeps every child that does not
end 0, as its row, program, command, exit status and the code heads of its lines. A listener hears every call the
eleven registered rows make of the fifteen sealer functions, through the interpreter's own events, wrapping
nothing. Six rows judge: the entry and the register's bytes; the register whole, its counts divided as the entry's
own sentence says; every registered requirement standing in the gate's text and in the cited texts; the 1,103
endings seated in their 77 groups; the 73 planted records refused, 55 one mutation from an accepted twin and 18
still owed; and a fence by source. Rowset `5b48184218214583`, 232 rows / 0 fail here.

Off the gate: 37 planted defects, 36 caught and one equivalent. Four of them left every earlier row green: a code
moved out of the head, a code grown longer, a plant dropped from a row, and a planted record changed in a second
field. The
listening instrument, run over the built gate, agrees with the gate's own row and hears no refusal raised by the six
new rows, so MINT-WATCH-0's register needs no amendment for them.

**On the host (2026-10-06): landed.** 0122 and 0123 were applied and the gate read `GATE PASSED`, rowset
`5b48184218214583`, 232 rows / 0 fail / 0 skipped. The owner pushed `a02d82c..a1c0a65`. The register an instrument had
heard there before the build is now held there by the gate's own rows, and the sealers' listener heard the
registered calls on the host's interpreter.

**Grade.** DECLARED: the idea, the rulings and the registration. OBSERVED (off the gate): the census, four
listen-only passes before the build (three here, one on the host), one over the built gate, the count of mints, the
mutation run. ESTABLISHED (gate, here): the six rows, 232 in the gate. MEASURED (host): the built gate, 232 of 232,
one run.
**does_not_show.** That a registered reason is the right reason: the court holds a refusal to its code, not to its
cause.

### MINT-WATCH-0 — every refusal raised inside the gate's own process, claimed · **built** (`cd1472ec`): four rows, 236 in the gate; the gate passes here and on the host
A separate slice by the owner's ruling. The full record is in [`verify/RUNGS.md`](../verify/RUNGS.md).

**What it is.** REASON-COURT-0's watch hears a child's ending. A refusal raised and caught inside the gate's own
Python never reaches it. This rung listens to the interpreter's own raise event, wrapping nothing, and holds every
refusal-class raise of a gate pass to a registered row, class, site and count. It adds visibility and no
vocabulary: it never says what reason a raise means.

**The rulings.** LOCK the listener as observation. REGISTER the watch. DEFER a reason code on an exception. REJECT
an observed class or site as authority for a reason. Then, in the fifth court:

1. **Sites from source, counts measured.** The inventory is read from the files' syntax: 8 refusal classes, 164
   raise sites in 15 files. Which row reaches which site, and how often, is a registered measurement of four
   configurations: 70 entries, 142,082 mints in 16 rows at 58 sites, all four agreeing. It is a baseline for drift
   and never the source of a reason.
2. **A site is its file, its function and the text of its raise**, under a pin of the file's hash. The line is a
   locator.
3. **Register now, build after**: this registration alone, then REASON-COURT-0's build, then this rung's.

**What the registration says beyond the rulings.** One mint is the gate's own plant and is registered as one. 105
sites were never reached and are registered as that. The rows measured are the 226 of today's gate: the rows
REASON-COURT-0's build adds must mint no refusal, or their entries come by an amendment. The watch never takes an
entry from its own run.

**Pushed (2026-10-05).** On the host the gate read `GATE PASSED`, 226 rows / 0 fail, with the entry and the register
in the tree, and the owner pushed `f145a8d..a02d82c`. With the push he ruled: the order stands and the registration
is not reopened; the register is a frozen measurement, under REASON-COURT-0's vocabulary and not under its
execution; the 105 sites never reached stay facts about reach and are not expectations; the scope stays as explicit
as it was registered; and this rung's build judges a pass against the frozen register and regenerates nothing.

**Built (2026-10-06).** One file changes, `verify/verify.py`; the entry, both registers, every program, every
sealer and REASON-COURT-0's six rows are as they were. The tap subscribes to the interpreter's own raise event as
the gate's file is read and keeps, of each refusal raised, a row, a class's name, a file, a line and a function.
Four rows judge: the entry and the register's bytes; the inventory against the tree's syntax, with no program run;
a fence by source; and last the watch, which holds every mint before it to the frozen register. It heard 142,083:
the 70 measured entries, each its count, and the gate's plant. Nothing is regenerated from the run. Rowset
`cb2f68e75e338768`, 236 rows / 0 fail here.

Off the gate: 39 planted defects, each caught, and two runs with no defect that pass. Seven of the nine that change
what is raised left every earlier row green. Two of those, a refusal raised and swallowed in a quiet row and a
second planted failure in the gate's own file, pass REASON-COURT-0's rows as well. One, a planted record that trips
another check of its sealer, is the drift the owner named: the same row, the same class, two counts moved.

**On the host (2026-10-06): landed.** 0124 and 0125 were applied and the gate read `GATE PASSED`, rowset
`cb2f68e75e338768`, 236 rows / 0 fail / 0 skipped. No push is in the output the owner gave. The refusals raised in
the host's own gate process were the register's, entry by entry: the configuration an instrument had heard there is
now held there by the gate.

**Grade.** DECLARED: the registration and the rulings. OBSERVED: the measured layer, one run in each of four
configurations, by an instrument outside the repository. ESTABLISHED (gate, here): the four rows, 236 in the gate.
MEASURED (host): the built gate, 236 of 236, one run. **does_not_show.** That any refusal is right; that a raise is
judged by anything; which input drew a mint; anything about a fifth configuration.

### The adjustment — the gates are finished; the design environment is the work · **declared** (the owner's, 2026-10-06); its first piece is built, off the gate, and has run on the host
With the host's 236 rows the owner brought two texts and the word *adjust*. Both speak to the assistant and not to
the reader of this file, so their rules are quoted and the rest is summarized. They restate the two times already
declared above (the gate certifies the program; content is admitted, not gated) and add an instruction: stop.

**The rule.**

> **The gate certifies the DESIGN PROGRAM. The user does NOT run engineering gates every time they design
> content.**

and its reason: *the purpose of finishing these gates is to earn the right to stop running them during design.*

**Two phases, kept apart.** The first was to finish REASON-COURT-0 and MINT-WATCH-0 as registered, without widening
either: no new cryptographic machinery, no general proof system, no reopened decision. That is done, on both
machines. The second is to build the design environment, with the gate out of the creative loop.

**The decision rule, for every gate proposed from here on.**

| what it is | what happens to it |
|---|---|
| an engineering invariant | registered, built, gated, frozen |
| a content or design operation | no full gate: it uses machinery already certified |
| observability or a diagnostic | measured, and never made authority |
| an experiment | kept off the ladder until recurrence justifies promotion |

*Do not create gates merely to make the project look rigorous. The rigor is valuable because it allows the product
to stop gating ordinary creative work.* The text asks that six words be kept apart: REGISTERED, MEASURED, BUILT,
GATED, CERTIFIED, DEFERRED. A registration that is not built is not proved; a preview is not authority; a model's
proposal is not truth.

**The path, as the text draws it.** Human, model, script or interface; a design proposal; a typed design
representation; a bounded verifier that admits; a session event; the world's authority; the renderer. *Language can
propose. The verifier admits. The session records. The kernel renders.* A model never runs code, writes files,
changes canonical state or bypasses the verifier. *Preview is state. Preview is NOT authority.*

**The product test.** A person says: make this room larger and add two entrances. A model proposes a bounded
design. It compiles to typed operations. The verifier checks bounds, capabilities and authority. The result is
shown. The person accepts. The session records the admitted operations and the renderer shows the new world. *No
full engineering gate runs here.*

**The surfaces the text lists**, against what stands today.

| surface | today |
|---|---|
| viewport, camera, mouse look | built: the live editor's window, on the host |
| proposal and preview; current against proposed | built off the gate, as text from above: `design/`. Not in the window |
| the same path for every editor | built: a key press and an admitted proposal make the same edit event (`admit-replay` holds it) |
| capabilities | built: ADMIT-0's grant, on the admitter's command line |
| command surface for a person or a model | built off the gate: `design/design.py`, five verbs |
| undo | built off the gate: the project steps back to the session before; nothing is deleted |
| inspector, parameter rack, design diff as objects | none: the world holds cells and five tile classes, and no objects |
| constraints with witnesses | none. `design/` reports readings and says they are not constraints |
| recipes | none beyond the design text's five statements |
| view modes beyond the frame and the text top view | none |
| portable project, compatibility inspector, plugins, observatory | none |

**The second text: a skill as the first editor.** It proposes that the first consumer of the path be an assistant's
skill, *a Verðandi editing operator, not a general coding skill*, with five capabilities: inspect, propose, preview,
admit, undo or revise. Its rule: *Claude should never edit the world directly. Claude edits through Verðandi's
design language*, so the skill need not be trusted as part of the kernel. It asks that the assistant query the
environment instead of carrying the world in its context, and that the interface and the assistant be one editor:
the same operations, the same admission. The owner's question with it: *maybe the move?*

It is the move that was taken. `design/design.py` has those five verbs and nothing else of substance, and each of
them rests on the certified shell. A skill is then a page of instructions for driving it, and a person at a
terminal or a script drives it the same way. The skill is the owner's to keep in his own assistant: it is not a
file of this tree.

**What was measured in building it (off the gate, one run, the build container).** A design of 60 cell operations
took about 20 s to preview and about 20 s to admit. One admission cost about 0.06 s on an empty session and about
0.9 s on the session of 60 edits. ADMIT-0 admits one operation per proposal and one proposal per run, and verifies
the whole session each time, so a design costs more than in proportion to its size. That is not interactive.

**What stands against the tree, on reading the two texts (a review, not a ruling).**

- **One engineering invariant is in sight, and it was found by measuring.** A proposal that carries a bounded list
  of operations, admitted in one run as one design event or refused whole. It changes the certified program and
  its language, so by the decision rule it is registered, built and gated. The ladder already names the place:
  DESIGN-EVENT-0.
- **A preview in the window is a program change too.** Showing the proposed world beside the current one in the
  live editor, with accept and reject, is new code in the shell. It follows the batch, as LIVE-AI-EDIT-0 and the
  branch were ordered.
- **Objects and constraints are not there to be inspected.** The second text's example shows a room of 14 by 10
  with one entrance and three ticked constraints. The world holds cells. By the rule already recorded, which kind
  of object is authority and which is a view is ruled kind by kind, and a constraint's status is a witness and not
  a stored field. Until then the tool says what it reads and calls it a reading.
- **The first text's first part repeats work that was done.** It names the registration, the listen-only pass and
  the two builds as still ahead. Its gate command is not this tree's: the gate is `python verify\verify.py`, and a
  landing here is three passes with identical logs.
- **Undo is a pointer.** A session is never modified, so stepping back means standing at the earlier file. The
  later one stays on disk, sealed.

**Grade.** DECLARED: the adjustment and both texts. ESTABLISHED (off the gate, by the tool's own ten checks): the
five verbs over the certified seam. OBSERVED (one run): the cost above. **does_not_show.** That a model writes
useful designs in this text; that the loop is fast enough to design in; anything about the window.

### DESIGN-EVENT-0 — a design as one transition · **built** (`ae7cbb36`): six rows, 242 in the gate; the gate passes here and on the host; pushed
The adjustment above ended with one engineering invariant in sight, found by measuring: a design of 60 operations
cost about 40 s through a seam that admits one operation per run. This section records what happened next: the
host ran the tool, the owner locked the rung, a court settled its shape, and it was registered. The rung's own
record, with the language, the checks and the rows, is in [`verify/RUNGS.md`](../verify/RUNGS.md).

**The host ran the design tool (2026-10-06).** With 0126 and 0127 applied the owner ran `new`, `grant`, `propose`,
`preview` and `admit` on a room with two entrances and a painted floor. The tool compiled 60 operations, the
shell admitted all of them in the scratch root and then for the project, and the session went from head
`73571153c2fc` to head `c18a71f6af8d`. Those are the heads the build container had reached from the same text. The
loop is the certified seam's on win32 as it is here. The output gives no time, and no push.

**The owner's text, and his lock.** It speaks to the assistant, so its rules are quoted and the rest is summarized.

> **Batch the next rung—but don't batch seven unrelated courts into `DESIGN-EVENT-0`.**

The seven properties it names are faces of one claim, in its words: *a design is an atomic, deterministic,
replayable, previewable transition rather than a pile of shell mutations.*

| | the property | the text's rule for it |
|---|---|---|
| 1 | one proposal, one admission | the whole proposal becomes one design event, or nothing does |
| 2 | a batch means its operations in order | *batching without creating a second semantic engine* |
| 3 | what is admitted is the net change set | redundant operations may exist in proposal space; admission records the canonical set |
| 4 | what was previewed is what is admitted | *No recomputation against a silently changed world.* A stale anchor is refused |
| 5 | incremental verification: *verify the delta, not the whole history* | *Do not weaken the canonical session semantics merely for speed. The fast path must be equivalent to replay.* |
| 6 | a preview is not a second world | the same batch projects into scratch state without touching authority |
| 7 | every editor speaks the same event | mouse, buttons, text, a recipe and a model all produce the same design event |

Three more rules from it. *The performance result is not itself the correctness theorem. The correctness theorem
is equivalence; the speedup is the consequence you measure.* On the tool as built: *Don't let Claude optimize the
current `design.py` by merely issuing fewer shell calls. Make **the event batch itself** the architectural object.*
And the order after: `DESIGN-EVENT-0 → DESIGN-IR/DIFF → LIVE-AI-EDIT-0 → GUI`, with the fifteen pivots of the
development environment left DECLARED and none of them made a gate.

> **My ruling: LOCK DESIGN-EVENT-0 as the next rung, and batch these seven properties into that court.** Don't add
> a separate gate for each theorem.

This also answers the question he had reserved: whether a design representation is promoted ahead of
DESIGN-EVENT-0. It is not. The event comes first and the representation follows it.

**What the tree said before the court.** Five facts shaped the questions. A head is folded once per event, so one
log item folded once cannot have the head of N edits. All three verifiers refuse a repeated proposal id and any
language but VRDNP1, so a batch changes them whatever its shape. Every edit re-hashes the tiles' 983,048 bytes, a
cell edit included, and that is the 4 ms an edit event costs on load. The kernel's lattice is 48, so no batch above
2,121 operations can be admitted. And the two refusal rungs pin the files a batch has to change.

**The court.**

| the question | locked | the owner's refinement |
|---|---|---|
| what a design event is in the log | N ordinary edits appended by one admission | *"one design event" should not mean "one hash fold."* The batch is the transaction boundary. The N edits are N log items, and the registration says so |
| what batches the language accepts | canonical batches only | the compiler canonicalises, never the authority. The normal form must be idempotent. An inverse pair is refused because a batch is a net change set, not because an inverse edit is illegal |
| what "verify the delta" means in this rung | full replay of the parent, with an exact memo | the delta claim is deferred. The memo is not a checkpoint and adds no trust root |
| what a preview is at the seam | a dry run of the admission, writing nothing | the dry run returns what binds it to the admission: parent head, digest, proposed head, language |

The third answer corrects the fifth property. His text had asked that a design operation not re-verify the whole
growing session *if the existing architecture can establish a checkpoint/parent invariant*. It cannot yet: a
session's seal is a hash, and nothing in the tree makes an earlier verification something a later run may rely on.
His court wording, registered as given: *Every admitted batch is replayed against a verified parent; unchanged
witnesses may reuse their exact prior digest, but no historical computation is trusted merely because it was
previously verified.*

**What is registered.** A canonical batch of one to 4,096 typed operations is refused whole or admitted by one
admission as that many ordinary edit events, equal in world, head, replay and saved events to the same operations
admitted one at a time through ADMIT-0. The language is VRDNP2, beside VRDNP1 and not in place of it. The preview
is `shell design --dry-run`, and an admission can be bound to it. One head is registered before the seam exists:
the 60 operations the owner admitted one at a time on his host have to reach `c18a71f6af8d…1036` as one batch.

**A prototype, before the registration was committed.** The seam was prototyped against the draft, outside the
tree. It reached the registered head, which had been fixed beforehand. It also found a plant in the draft that could
never have caught anything: a memo kept stale by a tile edit leaves the content unchanged, and the seam refuses an
edit that changes nothing, so no file would ever have reached the workshop. The plant was rewritten before the
commit. Run against the gate as it stands, it passed 229 of 236 rows, and the seven it reddened are each
accounted for in the registration. One run, OBSERVED: the 60 operations previewed in about 0.03 s and admitted in
about 0.08 s. That is a prototype's time on the build container and not a measurement of the build.

**What it costs the gate.** Six rows, 236 becoming 242 with the build. Two amendment entries, because
REASON-COURT-0 and MINT-WATCH-0 pin files this rung changes: that is the price the two watches named for
themselves. And two fences re-pinned on purpose, LIVE-INPUT-0's and LIVE-AUTHOR-0's, because each holds by its
text the statement the memo replaces; what they held there moves to a comparison of values in this rung's replay
row. It is one rung with one court, as ruled.

**Pushed, locked and built.** The owner applied the registration, the host's gate read 236 of 236, and he pushed
(`a1c0a65..b975fc5`). His lock with it: *LOCK / PUSH registration*, and *Don't enlarge the rung. The build now has a
very crisp job: prove the registered transition, especially the memo equality and whole-batch crash boundary.* The
build did that and nothing more.

| the claim | what holds it now |
|---|---|
| a batch is the same operations one at a time | five batches against ADMIT-0's own admissions; the 60 reach the head registered before the seam existed |
| a batch is whole or nothing | twelve planted deaths; 28 forged files refused by the shell, the workshop and the sealer |
| what was previewed is what is admitted | the dry run is the admission's own run, ended before anything is written; an admission bound to another digest or head is refused |
| replay stays the authority | the memo beside the computation that keeps none, over 2,208 edits; a wrong memo, which the shell carrying it reads back as verified, found by the comparison and refused by the workshop |

Two findings of the build are worth keeping. A registered case had been left out of the first rows, and a mutant
showed it: an unenveloped event inside a batch was refused by its neighbours' places and never by its own rule.
And the wrong memo fools the shell's read-back only where the parent's own history replays the same under it: a
plant depends on what it is planted into.

The design tool now sends one batch for one design. The owner's 60 operations, observed on the build container:
preview 0.10 s and admit 0.13 s, where each had taken about 20 s. That is one machine and no row holds it.

**Landed and pushed (2026-10-06).** The owner applied the two amendments, the build and its record. The host's gate
read 242 of 242, rowset `aa94c886190510c7`, and he pushed (`b975fc5..7e1d997`). The output holds one run. His word:
*push the build. Then don't immediately add another theorem. Let the full ×2 gate judge DESIGN-EVENT-0 as a complete
engineering rung.* So the rung stands as a whole and nothing is stacked on it yet.

Two more host runs followed, each after a patch of documents only (0133, then 0134). The gate read 242 of 242 both
times and he pushed (`7e1d997..eba1951`, then `eba1951..5f8ab66`). The three outputs read the same, row for row, and
so does the compact log here. All were the compact run, so what agrees is what was printed. The runs are listed, one
line each, in [`verify/RUNGS.md`](../verify/RUNGS.md).

That is agreement, and the owner then said exactly what it is not (2026-10-07). He replaced the phrase "full ×2"
with a predicate: **FULL×2 iff `TreeID₁ == TreeID₂` AND `GateOut₁ == GateOut₂`**, with identity in three values,
same-tree, different-tree and not established. *`==` earns the claim; `!=` defeats it; unknown withholds it.* Each
of the first three host runs followed a patch, so no two were on one tree: three agreeing runs, and not FULL×2.
Here two passes on one tree gave one log: FULL×2. The gate prints nothing of the tree, so a tree's identity is
taken outside it.

Then he ran the host's gate to the predicate (2026-10-07). With 0135 applied: Git's id of the tree and a status
that lists nothing, the gate, the gate again, the same id and the same empty status. 242 of 242 both times, and the
two outputs the same as printed. Same tree, same output: FULL×2 on the host. The identity is Git's, so the files
Git ignores are outside it; the outputs were compared as he gave them. No push was in that output. It came with
the next run, a sixth, on the tree with 0136: 242 of 242 again, pushed (`5f8ab66..83b0261`, carrying 0135 and 0136).

His word after it: *take next.* By his order the rung after this one is DESIGN-IR/DIFF. It is not registered.

Three things he fixed with it.

The times stay what they are. *The one thing I would not do is turn the 0.10/0.13 s container timings into a row.
Keep them as development measurements. The Windows journal-flush cost remains an explicit performance unknown.*

The memo's account keeps its whole chain, as he drew it: a wrong memo; the shell's read-back, which can be fooled;
the independent comparison, which catches it; the workshop, which catches it; an honest shell, which catches it.
*It establishes why the memo comparison exists at all.* The second step holds only on a parent whose history has no
cell edit after a paint, and the court plants it there on purpose.

And one idea is deferred by name. It is not part of DESIGN-EVENT-0, and it is recorded in his words alone:

> **DEFER — batch-proposal independent reconstruction.**
> The verifier does not reconstruct VRDNP2 proposal bytes from admitted events or independently recompute the
> proposal digest. Doing so would introduce a second VRDNP2 writer into the verification path and is outside the
> present admission boundary. Reopen only if durable independent provenance of the original proposal bytes becomes
> a requirement.

**What stays declared.** LIVE-AI-EDIT-0 and a graphical editor, in that order. The fifteen pivots. (DESIGN-IR/DIFF-0
was registered on 2026-10-07: the next section.)
That every editor speaks the same event: one consumer exists, the design tool.

**Grade.** DECLARED: the lock, the court and the registration. ESTABLISHED (gate, the build container): the six
rows. MEASURED (host): the registration's gate, 236 of 236, pushed; the built gate, 242 of 242 on each of its
runs, pushed, and FULL×2 by the owner's predicate on the two that ran on one tree.
OBSERVED (the owner's host, one run, off the gate): the design tool's loop over ADMIT-0 and the two heads. OBSERVED
(the build container): the times.
**does_not_show.** What an admission costs on the host, that the design tool has sent a batch there, or that a
model writes a useful design.

### DESIGN-IR/DIFF-0 — the compiler, certified · **built** (`2baa42f3`; its round named before the build, `c414587d`; two amendments with the build, `d51b4d20` and `42ac51f5`): five rows, 247 in the gate; on the host 247 of 247, FULL×2, pushed; a third amendment after it (`38b51bed`)
DESIGN-EVENT-0 made a design one batch and left one link outside the gate: the program that turns a design into
that batch. This section records the word that took the rung, the court that shaped it and what was registered.
The rung's own record, with the language, the codes, the rows and the plants, is in
[`verify/RUNGS.md`](../verify/RUNGS.md).

**The word.** *take next* (the owner, 2026-10-07), when the host's gate was FULL×2 on DESIGN-EVENT-0 by his own
predicate. By his order of 2026-10-06 the rung after the event is the design representation and its diff.

**What the tree said before the court.** Six facts shaped the questions. The compiler is the uncertified part, and
ghost G28 names it. A diff already has a registered language: a VRDNP2 batch is a net change set with one byte
form. No design object exists: a room is a statement that expands to cells. Not every difference between two worlds
is a batch, since the session accepts stair cells and VRDNP2 only opens and closes. His deferral of 2026-10-06
bounds any diff: it may be computed to propose and never wired into verification. And the rules already recorded
for a design representation hold: earn the authority, a status is a witness, a compiler in the tree is program.

**The court.**

| the question | locked | the owner's refinement |
|---|---|---|
| what is certified first | the compiler | not the diff alone, which VRDNP2 already is; not persistent objects, which are *an authority-model redesign, saved-form question, and identity/provenance question simultaneously* |
| where it lives | the certified shell, with an independent reference in the gate | *design/ is a client of the certified shell compiler, not the authority and not the court* |
| provenance | the proposal id is the digest of the exact design bytes | no saved-form field; a commitment, recoverable only while the bytes are kept; no per-operation attribution |
| readings and constraints | out, by name | *"the compiler produces the right diff"* is one claim; adding that the world satisfies a constraint system is another |

His closing: *I would LOCK all four and resist adding a fifth theorem to DESIGN-IR/DIFF.*

**What is registered.** The current design text, `VERDANDI-DESIGN 0`, is the source language, pinned at the byte.
`shell design-compile` reads a design and a saved session and writes the one canonical VRDNP2 batch for the net
difference between the session's world and the world the statements describe, or refuses with a code and the
design's line. It never approximates: a border cell opened, a stair written over, the camera's cell closed and an
empty change set are refusals. The proposal id is the SHA-256 of the design's exact bytes, which the admission
already seals beside every event. The gate holds the compiler three ways: against an independent reference, byte
for byte; against the statements applied by the gate itself to the parent's bytes, by content, through the
admission; and against ten planted compilers.

**A reference, before the registration.** The reference was written first and run against the shell as built. It
fixed the registered id, digest and content, and it found three things. A plant bites only on some designs and
parents, so each is run where it bites. The admission admits a batch that closes the camera's cell and one that
opens a stair: two of the tool's three "predicted" refusals were never the seam's, and are now the source
language's by registration. And a design's bytes can be admitted once in a history, by the session's rule on a
repeated id.

**What it costs the gate.** Five rows, 242 becoming 247 with the build, and an amendment for REASON-COURT-0's pins
on the shell's sources. One sentence of DESIGN-EVENT-0's entry is read more narrowly than it was written:
canonicalising never belongs *to the shell* is taken as a statement about the admission, which still rewrites
nothing. The registration says so, and it is the owner's to strike.

**Applied on the host, read, locked and batched (2026-10-07).** The owner applied the registration and its record;
the host's gate read 242 of 242, and the output holds no push. He read the entry and struck nothing: *I would push
0138/0139*, with one caution, that the camera's and the stair's rules must not be promoted into authority law. The
entry already says they are the source language's alone, and they stay so. He locked one predicate before the
build: the shell's bytes are the reference's, and the batch applied to the parent is the design's target. The
first is byte equality and the second is equality of the world's content, and the plants attack each side. The
amendment adds one plant for the second side alone: the same omission in the compiler and in the reference, so
that the bytes agree and only the content can catch it.

His second text named the round. DIFF-0 is the principal rung. Around it are four subcourts and two supporting
courts, *not seven new claims*: the refusal boundary, the batch's meaning, the id's commitment to exact bytes, and
a fence that keeps the design tool from becoming a second compiler; then the round trip and a mutation campaign.
They are registered as one amendment before the build (`DESIGN-IR/DIFF-0a`, `c414587d`), which adds cases to the
corpus and no row. The client fence sits in the tool's own checks, off the gate, because his locks leave it no
other place: nothing under `verify/` reads `design/`, and the tool is not certified.

One question he carries forward and rules out of this rung: *Should camera/stair validity be an authority
invariant, or deliberately remain a property of the design language?*

**What stays declared.** LIVE-AI-EDIT-0 and a graphical editor, in that order. Design objects that outlive
admission. Constraints. The fifteen pivots.

**The build (2026-10-07).** The compiler is in the shell, as a command apart from the admission, and the gate
holds his predicate with it: the shell's bytes are an independent reference's, and the batch applied to the parent
is the design's target. Every value registered before the compiler existed is reproduced by it. Five rows, 247 in
the gate.

Three things the registration did not foresee, each ruled by him the same day in three texts he brought.

| what the build met | his ruling |
|---|---|
| a row that held an amendment's pins against the file as built: the first later amendment breaks it | the amendment chain, accepted as a law: an amendment starts where the one before it ended, and the last is the built file's. *Not an exception to the invariant. It is the invariant correctly stated* |
| a row that held its six rows as the gate's last six | the anchor, accepted: the six that follow the 236. A historical position, not the ledger's end |
| a planted defect that survived every row: no parent of the court stood on a stair | the corpus extended by that one parent, the defect and the reason recorded, and nothing beyond it |

He rejected a semantic diff for this rung and any extra row, and gave one principle for all three: *history is
immutable; state may evolve; transitions must preserve provenance.* Three layers stay apart: history, identity,
behaviour. He asked whether the tree already held his relations. One it did not: that every pin is the first
court's own or is reached from it by named links. The origin of the pins is now registered and held, with no row
added.

The design tool no longer computes a change set. It hands the design's bytes to the shell and keeps what the shell
writes. A mutation campaign off the gate planted 97 defects: 85 of 94 first-order ones are caught by the rows that
run the compiler, four only by a reading of the source, five are equivalent because another check covers them, and
one was the hole the stair parent closed. The record, with the tables, is in
[`verify/RUNGS.md`](../verify/RUNGS.md).

**Grade.** DECLARED: the word, the court, the registration, his reading, the amendments, his three texts and
rulings. ESTABLISHED (gate, the build container): the five rows, 247 in the gate. OBSERVED (the build container,
one sitting): the mutation campaign, the tool's own checks, the times. MEASURED (host): the gate with the
registration applied and with the first amendment applied, 242 of 242 each, one run each; pushed
(`83b0261..5c8ad19`, carrying 0137 to 0141); the built gate, 247 of 247, two runs on one tree, FULL×2 by his
predicate, pushed (`11afebf..c8b6a1f`, carrying 0145 to 0147).
**does_not_show.** Equivalence for every design. That the reading the compiler and the reference share is what a
designer means: HERMENEUTICS-0 is registered for that. That the two machines hold one tree.

**On the host, and his fourth text (2026-10-08).** He applied the three patches, took Git's id of the tree, ran the
gate twice, took the id again, ran the design tool's own checks and pushed. The tree was one tree and the two
outputs read the same, so the gate is FULL×2 there on a tree that holds the compiler. The host's printed output is
the build container's log, line for line.

With the output he brought a text that rules on what had been put to him in private. Its distinction: *DIFF-0
should certify a state transition, not grow a general-purpose provenance system.*

| | his ruling |
|---|---|
| a ledger head | defer |
| validating every compile at content time | reject for this rung; a ghost (G29) |
| the registration's instrument as a layout | accept, inside the existing fence |
| the origin's digest, as a projection of 56 files | accept, inside the existing row |
| reading the chain on the host before the machines are compared | accept, as a protocol and not a row |
| a triple-write or meta-audit | defer |

The two acceptances that are mechanical are built into rows that exist (`DESIGN-IR/DIFF-0c`, `38b51bed`): over the
58 files the first reason court holds, what differs on disk from the origin is exactly what an amendment names.
No row is added. His last word on the rung: *I would stop adding architecture here.* The next rung's condition is
met, and it waits for his word.

### Hermeneutics and semiotics — what the design language means, apart from what compiles it · hermeneutics **registered** (`22d52d02`), semiotics **declared** (texts the owner brought, 2026-10-07); nothing built
Two texts the owner brought with the push of DESIGN-IR/DIFF-0's amendment, the second after he broke off the first
exchange. They speak to an assistant, so their rules are quoted and the rest is summarized. They seat nothing.

**The seam they start from.** DESIGN-IR/DIFF-0a says of its own predicate that a misreading of a statement shared
by the compiler and the reference is caught by neither equality. The first text: *a shell compiler and an
independent reference can agree perfectly while both implement the same mistaken reading of the language.* The
rung's direct target court *is itself another implementation of the registered description.*

**HERMENEUTICS-0, the first text.** Its question: *What is the authoritative meaning of VERDANDI-DESIGN 0,
independently of either compiler?* It sets two agreements apart:

```
  Compile_shell(D,S) = Compile_ref(D,S)        implementation agreement
  ⟦D⟧_S = Target(D,S)                          language-meaning agreement
```

| | |
|---|---|
| what it is | *A registered adjudication of the denotation of the source language.* Not *what the designer probably meant*, which *would immediately make the rung mushy* |
| the questions it would answer | whether a room is rim-closed and inside-open as registered; whether statements overwrite in order; whether a no-op paint is observable; whether a rectangle is the same set whatever the order of its corners; whether an entrance is merely a floor write; whether the camera's and the stair's rules are the language's or the authority's; whether the net change set is an encoding of the meaning or part of it |
| the camera and the stair | two questions there, which *need not be identical*: what the design language says, and what the world's authority permits. Not *silently making the compiler responsible for authority* |
| what he would register | a hypothesis, that the source language *has a determinate denotation for each admitted design and parent, independently adjudicated from the implementation of the production compiler and its reference*; and a court, *a semantic corpus written before looking at the compiler implementation*: for each construct a source, a parent, a semantic target, a rule and an ambiguity status |
| its plants | the ones DIFF-0 cannot tell apart: the compiler and the reference both wrong about a room, about overwriting, about corner order, about an entrance, about a paint or a net-zero design |
| its success | the court's meaning is the semantic target, and never *Meaning_court = Compile_shell*. *That independence is the entire point* |
| the strike | no *English-language "interpretation panel"*, and no model asked what a design means: *That would turn the semantic authority into an unbounded subjective oracle.* The owner registers the rulings *before implementation evidence* |
| a ruling's three values | *LOCK — meaning is fixed. DEFER — language is genuinely underspecified. REJECT — proposed interpretation is not supported.* Where a construct has two plausible meanings, *the correct result may be "underspecified", not a forced semantic answer* |

Its order, and its ruling:

```
  0140 DIFF-0a  →  0141 docs  →  HERMENEUTICS-0, registered  →  build DIFF-0  →  its court  →  FULL×2  →  build HERMENEUTICS-0
```

> **LOCK: introduce the concept now. DEFER: its implementation/build until after DIFF-0. REJECT: folding it into
> DIFF-0 or treating compiler/reference agreement as hermeneutic evidence.**

*Do not make HERMENEUTICS-0 a dependency of the DIFF build.*

**Semiotics, the second text.** *Semiotics is different enough that I would not fold it into HERMENEUTICS-0. It
sits one level earlier and asks a different question.* Its layers:

```
  SEMIOTICS       what does this symbol or construct stand for?
       ↓
  HERMENEUTICS    what does this particular design text mean, read as a whole?
       ↓
  SEMANTICS       what exact world-state does that meaning specify?
       ↓
  COMPILER        how is that world-state encoded as VRDNP2?
       ↓
  ADMISSION       is that encoded change permitted?
```

Its question of a token: *Why does the token `room` designate that kind of design operation at all?* A control, a
text, a model's proposal, a recipe, an icon and a sentence of intent are *different sign systems pointing toward
the same design authority.* It would not be another compiler court but *a language-design provenance court*: signs,
referents, conventions, overloaded terms, and the boundary between a sign and authority. And it is not to be
registered at once: *I would not register it immediately as a new engineering rung unless you find an actual
ambiguity that DIFF-0 cannot resolve.* Its summary, which also restates the first text's rung more cautiously:

| the layer | what the second text makes of it |
|---|---|
| semiotics | a conceptual layer, a vocabulary audit |
| hermeneutics | a registered interpretive court, if ambiguity appears |
| semantics | the exact target-world court |
| DIFF | compiler correctness |

*That prevents a dangerous collapse where "what the word means," "what the author meant here," and "what cells the
program changes" become one giant oracle.* And of a model at the seam: it *is fundamentally a semiotic translation
layer*, and *should never get to silently redefine what those signs mean.*

**What already stands that it would rest on.** The limit is registered: DESIGN-IR/DIFF-0's first limit and its
amendment's both say that agreement of the two programs shows one reading held twice. The meaning of every
statement is registered as prose, in that entry. One registered plant is of a defect the byte oracle cannot see
when it is planted on both sides; it is caught only because the target there is right.

**Where it meets rules already in force.** Each wants the owner's ruling before anything is seated.

- **A registered entry is not edited.** DESIGN-IR/DIFF-0's readings are pinned by `2baa42f3`. A ruling that reads a
  construct otherwise does not correct that entry; it makes a later language.
- **A registration needs something that can redden.** The court named here is a corpus of rulings, and the corpus
  is not written. Its targets have to come from the owner's rulings and from neither program.
- **The reference already exists.** It was written before DESIGN-IR/DIFF-0 was registered, by the hand that will
  write the compiler, and the registered cases were run through it. *Before looking at the compiler
  implementation* can be kept for the shell's compiler. It cannot be kept for the reference.
- **Language proposes, the verifier admits.** The strike of a panel and of a model as the semantic authority is
  that rule, one layer up.
- **The two texts differ on when.** The first would register the rung now, very small. The second would register
  an interpretive court if an ambiguity appears. Nothing is registered by this record.

**The third text, and the court (2026-10-07).** With 0142 applied on his host (the gate 242 of 242; no push in
that output) he brought a third text. It agrees that the trigger is met and says what to register: *an empty
`HERMENEUTICS-0` registration would be weaker than registering a small semantic corpus.* One registration, two
layers: the six readings as a denotation corpus, and four semantic laws beside it, *SEMANTIC-LAW-0 inside
HERMENEUTICS-0*, ratified only as *owner-ratified properties of the language*. Its fence: *the semantic target is
supplied by you before looking at the compiler's answer.* Its strike: *I would not register all six as
automatically LOCK.* And its measure of the thing: *You're trying to close one epistemic gap—independent
meaning—not build a new verification bureaucracy.* Semiotics stays where it was put.

The court was then held, and it did not go as designed. He ruled the first case himself, as registered. For the
second he asked for a search of the literature *for the wisest path*, and on the third and fourth he expressed no
preference. He was given one reading that covers all six, with a recommendation for each remaining case, and he
ratified all of it.

| what was ratified | |
|---|---|
| the reading | a statement is a constant partial map from targets to values; a design is those maps composed in line order, the later winning; the target is the parent with the map laid over it; the batch encodes the difference |
| two guards | no statement gives a frozen cell another value, the border being frozen at rock and a stair at itself; the target may not leave the camera's cell closed |
| six rulings | each LOCK, as DESIGN-IR/DIFF-0 registered them. None underspecified |
| four laws | corner order; fixed point; room as close and then open; exchange of statements that agree where both write. Each a theorem of the reading |
| the corpus | the six cases and three more: ten designs on the registered parent, each with a literal target typed by hand |

The reading borrows its shape from several fields at once, each attributed in the rung's record: writes that
compose as the lens laws describe, constraints checked immediately or at commit as a database does, changes that
commute as patch theory says, and refusal where a protocol would otherwise entrench a guess. That is why one
definition answers all six cases and yields the laws as consequences.

**What the registration says against itself.** Three things, each in the entry. Five of the six rulings are his
ratification of a recommendation written by the reference's author. The court was not blind to the reference in
four of the ten designs. And no plant is claimed to be caught by this court alone: read against DESIGN-IR/DIFF-0,
that rung's registered values appear to catch all five. What the court adds is adjudication and targets that are
the owner's.

**Grade.** DECLARED: the texts, the court's rulings and the registration; semiotics, declared only. OBSERVED (the
build container): the laws checked on the reference. MEASURED (host): the gate with the registration applied (0143
and 0144), 242 of 242, one run; pushed (`5c8ad19..11afebf`, which carries 0142 to 0144). Nothing of it is built.

### EVIDENCE-LINK-0 — a claim about a recorded event, traced to its source · **accepted as the next slice** (the owner's ruling, 2026-10-09); declared; not registered, nothing built

```text
  build evidence ──► recorded result ──► copied claim ──► published documentation
       checked            checked          unchecked
```

**Why.** The first stages are checked: the gate checks the tree, the witness the host, the recomputation the witness.
Copying a result into a commit message or a document is not. Six commit messages here named a wrong tree id when
first written (0150 to 0152, 0159, 0164 and 0165). Each was caught by hand, reading the message against Git's own
output, and corrected by a new commit before its patch was cut. None is in the pushed history; the reading that
caught them is not a check. His words: *the missing property is not another build check. It is provenance
preservation across the act of reporting.*

**His scope.** Mechanically checkable claims only.

| claim class | source of truth | check |
|---|---|---|
| commit and tree ids | Git's output for the named revision | exact equality |
| push range | the recorded output of the push | the endpoints agree |
| row counts and failures | the raw gate log | the parsed values agree |
| evidence hashes | the recomputed file bytes | SHA-256 agrees |
| prediction outcomes | the registered prediction and the retained run evidence | the result follows from the recorded criterion |
| documentation references | registered source records | every named value resolves to the intended source |

**The design choice he names.** Each claim's source is explicit. *A checker that merely compares one copied string
against another copied string can certify a consistently repeated mistake*: a message and a document carrying the
same wrong tree id agree with each other, and both must be held to Git's result for the named revision.

**His three adversarial tests, and the positive cases.**

| | the corruption | the checker must |
|---|---|---|
| wrong value | a documented tree id replaced by another valid-looking one | fail |
| wrong source | a claim pointed at another commit, whose tree id is valid and irrelevant to the run | fail |
| missing provenance | a row count or push range kept, its source record removed | refuse to certify it, never skip it |
| positive | one unmodified record for every supported class | pass |

**Its form.** An instrument outside the repository, as proposed: it reads evidence and reports discrepancies; it edits
no document and makes no commit. For each claim it names the claim, the value expected, the value observed, the
source record and the verdict. *Do not register a broad documentation linter unless these concrete cases
demonstrate the need.*

**Its boundary.** Not bundled into HERMENEUTICS-0: that rung is what registered material means; this is whether claims
about recorded events match their authoritative sources. Defined and registered after the current rung is
advanced: its scope, its mutation cases and its acceptance criterion written down first, then its predictions, then
the run.

**Acceptance (his).** Each supported class corrupted deliberately and caught; the unmodified records passing.

**Grade.** DECLARED: the ruling and the scope. The six messages are a count taken from the build notes kept outside
the repository; nothing is built. **does_not_show.** That a claim the checker cannot parse is true: it checks the
structured facts the project repeatedly copies, not every sentence.

### LiDAR — a sensor that observes the authoritative world · **declared** (the owner's ruling, 2026-10-09): the first slice recorded; not registered, nothing built

```text
  World + Sensor State + Scan Input ──► Canonical Returns + Evidence       (his sensor contract, eventually)
  the renderer may draw the returns; it does not become their source of truth
```

**His ruling.** Keep LiDAR work focused on making the sensor's relationship to the authoritative world measurable,
deterministic and falsifiable, *not merely improving point-cloud appearance*. Defer it until INPUT-0a and G33 are
closed. *Don't build a generalized sensor framework until one concrete LiDAR defect demonstrates the need.*

| slice | what | his placing |
|---|---|---|
| ray-to-world consistency | each ray a canonical origin, direction, range interval and hit or miss, held against the authoritative geometry; any discrepancy with a defined cause | first |
| deterministic returns | frames, units, precision, scan order, range quantization, tie-breaking between equally near surfaces | first |
| occlusion and visibility | nearer opaque geometry hides farther, at shared edges, thin barriers, corners and grazing angles; adversarial cases, not inspection | first |
| observer noninterference | the world before and after a scan; an active sensor's effect an explicit input | first |
| environmental independence | irrelevant surroundings perturbed, the canonical scan compared; legitimate dependencies declared | with the court he deferred |
| reconstruction | what a scan establishes apart from what a reconstruction infers: a missing return does not prove empty space | later |
| sensor realism | | later |

**Considered against the tree.** One ray law exists: the kernel's walk of a ray through the cell lattice, held to the
frozen oracle on both machines (`kernel-oracle`, `gauntlet1c-dda`, the bearing camera's rows). It is integer, it takes
the first cell hit, and what it witnesses today is a frame's digest, not a range per ray. A LiDAR here would read that
law as data; whether it needs a second law is what the first slice would find.

**Grade.** DECLARED: the ruling. **does_not_show.** That any return the kernel computes is a range a sensor would
report.

### A claim and its evidence — four layers · **declared** (two texts the owner brought, 2026-10-09); his rulings in the first are kept; nothing built

**The first text.** *Verðandi should not confuse a declared contract with a demonstrated property, or a recorded verdict
with trustworthy evidence.* Four layers, not to be conflated: the **contract** (what is claimed, from which inputs,
prerequisites and surroundings); **validation** (are the declarations well formed: prerequisites present, the graph
acyclic); **adversarial evidence** (does the claim survive mutation, isolation, order, perturbation, another machine);
the **certificate** (which observations support the verdict, and can another reader rebuild it). And what each layer
does not give: *a valid dependency graph does not prove dependency completeness*; a passing row is not shown to be
independent of the rows before it; matching outputs are not shown correct; a clean status at two ends does not show
that nothing changed between them. His rule:

```text
  declare the contract  ──►  validate its structure  ──►  attack its completeness  ──►  preserve the evidence
```

| his ruling | in his words, or close |
|---|---|
| the witness | ACCEPT the design, REVISE the evidence boundary, keep the predicate unchanged. Status and tree id are complementary evidence, not substitutes. A manifest of the files hashed one after another is not an atomic snapshot: describe the guarantee as matching observations at the boundaries |
| G33 | INVESTIGATE FIRST: an intended prerequisite, an accidental dependence on state an earlier row left, or a defect of the row itself. Register only the demonstrated contract; *if it is accidental, do not institutionalize it as a prerequisite*. A validator can show the declared graph well formed; it cannot show that every real dependency is in it |
| normalization | DEFER as a replacement for FULL×2. Byte identity and an equivalence `∼` are two predicates; a semantic one only for a demonstrated variance, naming the field, with mutations that show meaningful differences still fail |
| what comes after | the general dependency-completeness court deferred; G33 to find the smallest useful next slice |

**The second text.** It reads the first beside a proposal for a GPU backend, which was not brought here, and ranks
them in two tiers: the witness, G33 and byte identity first; the GPU work later, under the same courts. It proposes one
evidence format for every layer, a discovery of dependencies by running each row with each other row, and courts for
a GPU backend (shader against the CPU reference, pixel-exact frames, two platforms, two drivers).

**Set against his rulings and the tree.**

| the second text | what stands |
|---|---|
| discovery by running every row with every other, a prerequisite registered after three counterexamples | the broad isolation mechanism his rulings defer (*do not add a broad row-isolation framework yet*); and a count of counterexamples does not decide between an intended prerequisite and an accidental one, which is what he asks first. G33 was settled by seven cases on one row |
| *Fixed-point Q32.32 logic* as the tree's counterpart to fixed-point shaders | the tree's Rust holds no Q32.32. Its laws are integer: the tick law, the bearing camera. Fixed point appears only in the frozen oracle's game tools |
| *RHI Firewall* | no counterpart in the tree. The nearest is the shell, which presents and holds no authority |
| *PRESENT-EXACT-0* readback, READER-COURT-0 as two languages | they exist: a presented frame read back and compared exactly; two readers of one saved form |
| a unified evidence format | the witness's files and their manifest are one, for the host's runs; the rows keep their own |

**Grade.** DECLARED: both texts; his rulings in the first. Nothing was computed for this section beyond what G33's
investigation records (RUNGS, INPUT-0).

### REFLEX — a reflexive semantics: authority, perspective, effect, environment, observation, reconstruction, intervention and certification as relations · **declared** (two texts the owner brought, 2026-10-08, after a research report put to him in private); considered at his word; not registered, nothing built

```text
  knowledge flows up:      L0 world ─► L1 claims ─► L2 campaigns ─► L3 claims about campaigns
  authority does not flow down, unless it becomes an explicit input at L0

  observe freely ·  intervene explicitly ·  certify only from below          (his cardinal rule)
```

**The first text.** His judgement of what came before it: *still too conservative*. A per-row matrix of
environmental dependencies is one projection of something larger. In it:

| his element | in his words, or close |
|---|---|
| the object | `𝓡 = (A, E, O, P, D, L, τ, Γ)`: authority, environment, observer, the authoritative projection, declared dependencies, semantic level, a contract for failure and termination, an evidence graph. *A row is merely one executable instance of a claim*, and a claim's verdict is PASS, FAIL or UNDEFINED |
| one theory, not four | the world changing, the environment changing a verdict, observation changing the world, claims about claims: *four manifestations of dependency* |
| an effect footprint | `Eff(x) = (R, W, I, O, M)`: reads, writes, interventions, observations emitted, meta dependencies |
| backreaction | the scalar dropped for the set of counterexamples `BR_P(O) = {(s,T) \| P(T(s)) ≠ P(T(O(s)))}`, and observers classed by their reaction footprint, from a pure projection to an *unbounded observer*, which is inadmissible |
| lenses | an observer is `get` only; a participant is `get` with a lawful `put`; *illicit backreaction* is `get` with a hidden `put`. An observer has an effect signature, not only a return type |
| correction | *Any correction crossing from observer state back into authority must become an explicit authoritative input* |
| stratification | a finite truth table is possible; what matters is the level. A row may read another row's recorded result; it may not declare truth for claims that include itself |
| grounding | a graph of which verdict depends on which; grounded recursion allowed, with `⊥` where a claim is not grounded: PASS / FAIL / UNDEFINED, a least fixed point |
| the reflexive certificate | sound over a domain iff seven things hold: authority closure, environmental noninterference, observer transparency, observer fidelity, reconstruction (`Replay(Seal(A)) ∼_P A`), groundedness, and an endorsement path computed by an implementation independent of the path that produced the claim |
| a certificate as a graph | who may observe whom, who may change whom, which environment may matter, which claims rest on which evidence, where the last endorsement comes from |
| Kross | a naming system only: *rights decrease as perspective increases* |
| a capability lattice | 1P read, write, commit; 2P read, propose; 3P read, observe, reconstruct; L2 inspect, mutate in a campaign, compare; L3 certify about L2. Nothing at L3 reaches the authority |
| the Adversarial Projection Principle | his name for *direct the perturbation; watch every row*: a perturbation may be chosen by a hypothesis about one observation, and is judged against the whole verdict vector, *so the investigator does not select both the weapon and the target* |
| a declarative perturbation | a claim declares what it reads and what it must not depend on; the compiler solves for the perturbations — a clock whose decimal or hexadecimal spells a literal, a path that holds it — and runs the whole-vector comparison |
| the matrix compiled | static, dynamic, directed, mutation, grounding and independence obligations derived from each row's declaration, *not documentation* but *executable semantics* |
| the identity | *Verðandi compiles not only a world, but the permitted perspectives on that world* |
| the arena | the same calculus would certify a map: whether rendering, a spectator or the folder can perturb what is authoritative in play |

His ladder, *a sequence of increasingly strong theorems*, and *I would not immediately build all of this*:

```text
  REFLEX-0  perspective types          authority, observer, reconstructor, intervener, court, meta; no behaviour changes
  REFLEX-1  effect footprints          declared against actual
  REFLEX-2  environmental independence the whole verdict vector under E → E′
  REFLEX-3  oracle-directed perturbation  a literal of an oracle solved into the environment
  REFLEX-4  observer transparency      observers off against on, the same authority inputs
  REFLEX-5  reconstruction             replay of the seal, equivalent over future traces
  REFLEX-6  grounded meta-claims       the claim graph built, ungrounded cycles refused
  REFLEX-7  an independent court       a checker that is not another run of the same checker
  REFLEX-8  the reflexive certificate  machine-readable: authority, effects, dependencies, perturbations,
                                       observations, reconstruction, grounding, independent endorsement
```

His ruling: the report's idea of a per-row matrix is good, and *the actual breakthrough is one level above it*: a
reflexive semantics of which the matrix is one projection.

**The second text.** Said to be *the operational mapping of this reflexive architecture*. It restates the first text
as four parts — dependency as one axis, observers verified by effect type, the boundary of correction and levels,
the graph of grounding — and closes with a table that gives each level of the tree a rung.

**Considered against the tree.** Each line is what stands. None is a proposal.

| the first text asks for | what stands |
|---|---|
| a correction becomes an explicit input | holds where an edit is made: *language proposes, the shell admits, the session records*. The design tool proposes and only the shell's admission writes; a host's state is attached after a label is fixed (`hoststate-fence`) |
| the capability lattice's 2P, read and propose | the design tool: it reads a session and proposes a batch; only the shell's admission writes |
| reconstruction, `Replay(Seal(A)) ∼_P A` | replay is the authority: sessions replay to their heads in rows (`sessionwalk-replay`, `livesession-resume`, `admit-replay`) |
| an endorsement path independent of the producing one | holds per row in many rows: the compiler against the gate's own reference (`designir-compile`), a Python twin of the movement rules (`input-replay`), two readers (`readercourt-agree`), the frozen oracle (`kernel-oracle`). For the gate itself, no: the host runs the same gate |
| a grounding graph | not declared. The rows run in one fixed order, and what a row takes from the rows before it is not written down |
| effect signatures for observers | none in the design language or the gate. `membrane-wall` refuses one path of writing, in memory, through a Reading |
| levels L2 and L3 | outside the rows, as his rulings keep them: the mutation campaigns, the class reading of G30, the host's reconstruction, the perturbed pass |

**Where the texts need care.**

- *Lenses.* The laws are Foster, Greenwald, Moore, Pierce and Schmitt's (2007): GetPut, putting back what was just
  got changes nothing; PutGet, getting what was just put gives it back; PutPut, a second put overrides the first.
  An observer that reads and writes back what it read satisfies GetPut. So no comparison of states or outputs can
  tell it from one that never writes; what tells them apart is the effect signature, as the first text says.
- *Grounding.* The first text gives an ungrounded claim `⊥` and keeps grounded recursion. The second makes the graph
  a DAG and a cycle red. They are two rules; which one is his.
- *The second text describes as done what the first declares.* Its words against the tree:

| the second text | what stands |
|---|---|
| *an unyielding, self-certifying machine* | the first text's rule is the opposite: *certify only from below*. Nothing in the tree certifies itself, by his own rulings |
| the write-back mutant *completely neutralized*; *rejected at compile-time* | nothing is built. No observer has an effect signature. A Rust shared reference forbids writing only for types without interior mutability, and files, the environment and statics are outside it |
| purity by construction, *completely removing the need* for runtime checks | the first text keeps dynamic testing as *the second line of defense* |
| a correction as an *explicit, authenticated input* | nothing is authenticated: a seal is a hash, not a signature (G16). The first text says *explicit authoritative input* |
| a row at L(n+1) *structurally blocked* from reaching down | held by rulings and by the rows' own design, not by a structure: nothing prevents a row from reading anything |
| a cycle caught, the gate red, *refuses to emit the binary* | no such check exists, and the gate emits no binary |
| L0 BEARING-FAST-0 and SIM-TICK-0, *the integer-locked, float-free physical substrate* | a rung is not a level: each rung puts programs at L0 and rows at L1. The tick law and the bearing camera are integer; there is no physics |
| L1 ADMIT-0 and DESIGN-IR/DIFF-0 | their programs, the admission and the compiler, are on the path of the authority, L0; their rows are L1 |
| L2 READER-COURT-0 and REASON-COURT-0, *dual-runtime cross-language parsing courts* | rows, L1. READER-COURT-0 holds two readers of one language to one verdict; REASON-COURT-0 holds refusals to registered reasons, and is not a parser |
| L3 MINT-WATCH-0 and the G30 audit, *absolute exception tracking* | MINT-WATCH-0 is rows, L1, and states its reach: 105 of 164 raise sites never reached, a mint not a judgment, the watch hearing up to its own row (G26). The class reading of G30 was outside the gate, L2 |
| *the standing layout of the active rungs transitions into its definitive configuration* | no rung changed. The ladder stands as before, and HERMENEUTICS-0 waits for his word |

**What stays declared.** All of it. REFLEX gathers what was declared before it: REFLEX-2 is the environmental
independence he accepted and deferred, REFLEX-0 and REFLEX-1 are PERSPECTIVE-0's laws as types and effects,
REFLEX-3 is the clock of G30 made general. Whether any becomes a registered rung, in what order, and against
HERMENEUTICS-0, is his.

**Grade.** DECLARED: the two texts and his ruling. ESTABLISHED (gate): the rows named above, as they stand.
OBSERVED: nothing was computed for this section.
**does_not_show.** That the seven conditions of the certificate can be held of this tree. That an effect signature
can be given to an observer in Python or in the design language. That a compiled matrix would stay small enough
to read.

### PERSPECTIVE-0 — what a system is, what it sees, what it models, what it may claim · **declared** (three texts the owner brought, 2026-10-08); considered at his word; not registered, nothing built

```text
  1P   execute       S ──T──► S′                          the transition
  2P   observe       S ──O──► (Y, S)                      the state unchanged
  3P   reconstruct   A ──R──► Ŝ ;  O(Ŝ) =? O(S)           another producer
  M    claim         a verdict about an observation, one level up
       the wall      no level holds a truth predicate for itself
```

**The three texts.**

- *Four sources toward one boundary.* Ethan Kross's work on distanced self-talk, abstracted to the separation of
  acting from observing; the Luenberger observer, which estimates a hidden state from outputs and is not the plant;
  the state monad as the plumbing; Tarski's undefinability of truth as the wall. His rulings in it: Kross ACCEPT,
  *provided the psychological claims aren't overstated*; Luenberger STRONGLY ACCEPT; the state monad ACCEPT; Tarski
  ACCEPT, *as a design constraint rather than a literal implementation theorem*.
- *The deeper version.* A perspectival machine `V = (S, F, Π, Ω, M, C)`: state, transition, perspectives,
  observations, models, courts. *No perspective inherits authority merely by being able to describe another
  perspective.* An observation with an error channel. Observational equivalence: two states that no permitted
  observer tells apart. A reflection tower in which quoting climbs a level and no level holds its own truth. Six
  laws: state authority, perspective non-collapse, observation purity, reconstruction agreement, reflection
  stratification, no internal truth oracle. And a killer mutation: *change an observation into an
  authority-bearing state transition while leaving its output unchanged.*
- *Backreaction.* An observer inside the system can change it. A passive observer returns the state it was given; a
  participating one does not, and must say so: *unmodeled backreaction = defect*, *declared backreaction = part of
  the program*. A reaction profile for each observer. Three equivalences: of state, of observation, of future
  behaviour. And a reflexive system, one whose representation of itself takes part in its own dynamics.

His word on all of it: *I would not build it yet*. A declared research rung first, *not immediately into code*.

**Considered against the tree.** Each line is what a row or a ruling already holds. None is a proposal.

| the texts' law | what already holds it |
|---|---|
| observing does not move the authority | `hoststate-fence`: the same raw record, sealed with no probe and with two different host states, gives the same label and reading. `mouselook-capture`: the window leaving the foreground changes nothing saved, and a control shows the same inputs do change it in the foreground. The design tool's preview: a dry run writes no session |
| an observer is not read back | `refusallog-fence`, `runledger-fence`: each log written by one primitive and read by nothing on the path, by source. `refusallog-bijection`: a log that cannot be written leaves a refusal's exit status and message as they were |
| perspective as a type | `membrane-wall`: an edit through a live Reading must not borrow-check, rustc's refusal is the row's pass, and `membrane-build` is its control |
| reconstruction agreement | `readercourt-agree`: two readers, one verdict on every single-byte mutant of three documents. `kernel-oracle`. `designir-equivalence`. The host's re-run of the whole gate |
| an environment declared irrelevant | `livesession-classify`: a shell built from sources with CRLF line endings names the same renderer. `simtick-equivalence`: inputs moved within their tick save byte-identical data |
| an observer's error is a result | each refusal carries a registered code; a host comparison where the chain fails is not interpreted (DIFF-0c) |
| no internal oracle | the mutation campaigns and the host's reconstruction stay outside the rows; reconstruction is *a test, not a fifth invariant* (DIFF-0c); every entry forbids reading *that registering a condition earns it*; a seal is a hash, not a signature (G16) |
| evidence is a declared projection | G30, in his backreaction text's words: *An observer must declare which projection of the world constitutes evidence* |

So the tree has met these laws a row at a time. What the texts add is a name for the class, and the demand that a
row say which perspective it holds.

**Where a formula needs care.** A reading here, with the outside sources it rests on.

- *The commutator.* `O;T ∼ T;O` cannot hold on what the observer reports: observing before a transition and after
  it sees two states, which is what observing is for. Compared on the authority's projection `P` alone,
  `P(T(O_S(s))) = P(T(s))`, it is his backreaction text's own condition of transparency. Asked of every transition,
  it is the unwinding by which noninterference is shown step by step (Goguen and Meseguer; Rushby).
- *Backreaction as a difference.* `Obs(T(S)) − Obs(T(O(S)))` needs observations that subtract. As the set of states
  and transitions where the two disagree, it asks for that set to be empty. A pair of runs refutes it; no assertion
  inside one run can.
- *Observation purity as `O;O ∼ O`.* That is the state monad's get-get law. An observer that reads the state and
  writes it straight back satisfies it as well (get-put), and so would the killer mutation.
- *Tarski's reach.* Truth for a finite language can be defined by listing its true sentences; Tarski's paper of
  1933 gives that definition among its examples. The wall stands against an evaluator of every claim a language can
  express, itself among them. The sharper reason a gate cannot vouch for itself is Löb's: a system that proves *if
  provable then true* of a sentence already proves the sentence. His qualifier, *a design constraint*, is what keeps
  the analogy honest.
- *Kripke.* A language can hold its own partial truth predicate when every claim is grounded. Read for a gate: a row
  may read other rows' outputs if the chain ends in the world. A cycle is the defect, not reference to itself.
- *Kross.* The studies (Kross and colleagues, 2014) set first-person pronouns against one's own name and
  non-first-person pronouns, pooled; second and third person are not told apart. A preregistered meta-analysis
  (Murdoch and colleagues, 2023; 25 experiments) finds a small benefit and calls it uncertain. The names 1P, 2P
  and 3P are borrowed. What the engineering claims rests on rows.
- *The host's re-run as the third person.* It is independent of the machine and its compiler, not of the checker:
  the same gate runs on both. Wheeler's diverse double-compiling earns its independence from a second, trusted
  compiler.

**What stays declared.** All of it. Whether PERSPECTIVE-0 becomes a registered rung, and where it sits against
HERMENEUTICS-0 and environmental independence, is his.

**Grade.** DECLARED: the three texts and his rulings in them. ESTABLISHED (gate): the rows named above, as they
stand. OBSERVED: nothing new was computed for this section.
**does_not_show.** That the six laws hold of the tree as a class. That a perspective can be made a type of the
design language's IR. Anything about the psychology of people.

### Environmental independence — directed environment perturbation · **accepted as a future audit mechanism, deferred** (the owner's ruling, 2026-10-08); not registered, nothing built in the gate

```text
  FULL×2              V(E) = V(E)                       two runs, one environment, near enough
  the host's re-run   V(E_host) = V(E_here)             another machine, the same gate
  his proposition     ΔE ∩ Dependencies(r) = ∅  ⇒  V_r(E) = V_r(E + ΔE)
```

**His ruling.** On the clock reproduction and the path probe of G30: ACCEPT as a future audit mechanism; defer
until after the host's result. *Do not add the directed court yet.* His names for it: *Directed Environment
Perturbation*, or *Environmental Independence Court*. The proposition is claim-relative, not that a row passes
under many environments: *A row may depend on its declared environment; it may not accidentally depend on an
undeclared environment.*

| his design point | in his words, or close |
|---|---|
| a matrix, not a list of literals | per row, the verdict at baseline and perturbed: clock in decimal, clock in hexadecimal, path, locale, timezone, separator, environment |
| `—` in a cell | *not applicable by construction*, never *we forgot to test it* |
| no aggregate | the output is the matrix, not a single pass. *That prevents the future court from becoming another opaque score* |
| legitimate dependencies kept | a row may depend on paths, separators, locale, clock, architecture, line endings or executables, when it declares them |
| a court of the class | perturbations generated from the audit's literals and dependencies, not one-off `4242` tests |
| the estimate | superseded as evidence by the controlled reproduction; the future window a detail of reproduction, never part of an invariant |
| a wider property | *Canonicalization must eliminate accidental environmental degrees of freedom*: a world must not depend on the folder it was compiled in |

**His order.** Accept the eight patches; finish the head's passes and the host's evidence; reconcile the host's
reconstruction against the chain precondition; only then decide whether this deserves a rung; if so, a court of the
class, its perturbations generated from the audit, verdicts held only outside a row's declared dependencies. The
first three are done (RUNGS, DESIGN-IR/DIFF-0: *The amendments on the host*). The fourth is his.

**A reading in his text, set right.** He reads the path probe as showing that *the same class of environmental
contamination exists beyond time*. It did not show that. Three rows were run in a checkout whose path spelled their
words, and all three passed: it found nothing.

**Observed since, off the gate (2026-10-08, the build container).** One whole pass of the gate on the head, every
perturbation at once, and the failures then bisected. The instrument is outside the repository.

| perturbed | how |
|---|---|
| the checkout path | `…/Urðr 4242 a private title the log must never hold focus pause capture blur foreground adopted/tree`: a space, a letter outside ASCII, the mock pid, the forbidden title, the five words about focus, the sealer's word |
| the wall clock | moved to 2041, past 2³¹ seconds, where every millisecond value begins `224242` for the whole pass |
| the time zone | `Pacific/Kiritimati`, fourteen hours ahead |
| the locale | `tr_TR.UTF-8`, built for the pass; its decimal point is a comma |
| the rest | umask 077; another home folder; Python's hash seed 4242 |

The pass: 243 PASS / 4 FAIL, and the tree's tracked files the same after it as before. `input-tamper`,
`input-not-authority`, `input-demo`: a walk's path is one word, and the path held a space (RUNGS, INPUT-0; G31).
`reasoncourt-watch`: its four findings are the input program's refusals, endings no group of the register holds. One
cause, four FAILs. Bisected with the rows run alone: a space, and nothing else, fails the three; `ð` alone passes.

Everything else held, among it the corrected `refusalwhy1-log` with each of its seven records' clocks holding the
pid's digits, and `mouselook-capture` and `presentexact-sealer` with their words in the path.

So the reading of the path probe was wrong and its conclusion right: where the tree is checked out does reach a
verdict. The probe that found nothing chose its rows by the hypothesis as well as its perturbation. The pass that
found it chose the perturbation and watched every row. FULL×2 cannot see this, and is not broken by it: both of its
runs share the folder. Nor can the host's re-run: the host's folder holds no space either.

**Prior art, found by search.** Paraphrased; nothing rests on it.

- Debian's `reprotest` builds a package twice with its surroundings varied — the time through faketime, the build
  path, the order of files, the locale, the time zone, the umask, the home folder and more — and compares the two
  builds. Debian's own continuous rebuild varies identity and environment between its two builds, no longer the
  build path, and makes the second build without the package's tests. Both vary builds and compare what was built.
  The verdict of a test is not what they compare.
- Noninterference (Goguen and Meseguer, 1982): what one party does must not change what another observes. His
  proposition has that shape, with the undeclared environment as the first party and a row's verdict as what is
  observed. Such a property is refuted by a pair of runs; no single run can refute it.

**What stays.** Accepted, and deferred. No row, no register, no entry. Whether it becomes a rung, and where, is his.

**Grade.** DECLARED: his ruling. OBSERVED (the build container): one perturbed whole pass and its bisection.
**On the host (later the same day).** One factor, the space, in a clone under `Verdandi space probe`: the four
rows named before the run failed, and no other (RUNGS, INPUT-0). The verdict vector is the container's.

**After the repair (INPUT-0a).** His ruling keeps the court deferred: *the G31 fix plus the two predicted perturbation
passes give you a useful, targeted end-to-end test of the method without prematurely building the court.* The
container's pass, run again on the repaired tree as predicted: 247 rows / 0 fail. The host's clone with a space, run
twice by the witness: 247 rows / 0 fail, FULL×2.

**does_not_show.** Any other factor on the host. A matrix: the container's pass changed seven things at once, and
only the space was isolated. That a factor no pass changed is harmless.

### A competitive arena — from a certified world to a map that matches are played on · **declared** (a text the owner brought, 2026-10-08); considered at his word; not registered, nothing built

```text
  the text's path     intent ─► canonical spatial state ─► derived world ─► executable constraints
                             ─► adversarial tests ─► reproducible match

  what stands today   design text ─► shell design-compile ─► batch ─► shell design ─► sealed session ─► picture
                      cells of a 48 lattice · five tile classes · two stairs · one camera · an integer tick law
                      no second actor · no shot · no height · no wire
```

One text, in three parts, and then the second part again by itself, as *the proposal*. His question: how does this
become a map like *Terminal*, one that competitive matches are played on. A proposal. Then a correction of it, in
another voice. Neither names its author. Nothing here is registered, nothing is built, and the order of the route
is unchanged.

**The proposal.** Its opening: a map like *Terminal* is made by visual iteration and playtesting, and this tree
*would require mathematical proofs of competitive fairness before a map ships.* It keeps the three layers, history,
identity and behaviour, and says of itself: *nothing new is invented — just extended to 3D space.* Its seven parts:

| part | what it proposes |
|---|---|
| 1. geometry | a source language `VERDANDI-GEO 0`: `block`, `cut`, `void` (integer, axis-aligned volumes), `plane` (three integer points), `spawn TEAM`, `objective TYPE`. No float, no curve. The hash stays the SHA-256 of the exact bytes; statement order is volume order; amendments name the geometry files changed |
| 2. fairness courts | four, each with a row: `sightline-balanced` (every spawn-to-objective path has equal average travel time), `spawn-safe` (no spawn sees an enemy spawn within two frames), `approach-diversity` (three distinct approaches to every objective), `raycast-consistent` (a ray is the same on every platform). Run by a ray server firing from a thousand or more sample points, with *exploit mutants*: a bot at every coordinate and a kill probability |
| 3. the network | lockstep simulation in integers: fixed-point positions and velocities, box collision; the whole state hashed after every tick on Linux and on Windows, and a map rejected for competitive use if the hashes part |
| 4. two phases | the gate's: the geometry text to a volume list and a collision mesh, with the fairness courts. Content time's: textures, light, the GPU mesh, unverified. A map changes its look without touching what is certified |
| 5. a map's amendment chain | a small tweak is an amendment and the courts run again; a rebalance is a new version with a fresh chain; an exploit is a hotfix by amendment or a version bump. *Never edit an already-shipped map's geometry* |
| 6. the map as an entry | an id, the geometry's hash, a digest of the courts' results, its amendments, a network version; a tournament licence embeds the digest, and a map whose hash does not match is disqualified |
| 7. its roadmap | *immediately, in DIFF-0*: the new language, a geometry fence, a sightline court. Next: the integer lockstep engine and the cross-platform state hash. Later: a digest signed by an authority, and third-party maps certified by passing every court |

What it says is lost: curved surfaces, floating-point movement, terrain destroyed in a match. What it says is
gained: a *mathematical guarantee that the map cannot be "unbalanced" by geometry changes*, reproducibility across
hardware, verifiable tournament integrity. Its contract lists four things verified (spawn-safe, sightline-balanced,
raycast-consistent, network-lockstep) and three not (texture, light, sound).

**The correction.** Its premise: *Verðandi should not try to mathematically prove that a map is "fair" in the
absolute sense.* Quality in a competitive map comes from geometry, movement, weapons, visibility, spawn rules,
objectives, timing and what people do with them. What the tree can do is make the map *a deterministic,
inspectable competitive object whose measurable constraints are provable and whose human-play properties are
experimentally falsifiable.* Its formulation: not *proves a map is fair*, but *makes the claims about a
competitive map executable.*

| the correction's point | in its words, or close |
|---|---|
| one source, many derived roles | a wall is at once a collision boundary, an occluder, a traversal boundary, cover and a landmark. Collision, visibility and navigation are *derived from the same canonical spatial source* and cannot drift apart |
| topology before geometry | a competitive map is a graph of navigable regions and traversable connections embedded in space. Reachability and the number of distinct paths are questions about the graph |
| sightlines as geometry | a visibility graph between regions, its edges annotated, in place of random rays |
| constraints, not fairness | precise courts: spawn separation, objective access, approach diversity, lane separation, cover continuity, dead-end exposure |
| three parts of quality | `CompetitiveMap = GeometricValidity ∧ ConstraintValidity ∧ EmpiricalFitness`, and *only the first two are theorem-like*. The third is match data and people, and *should never be falsely elevated into a mathematical theorem* |
| the renderer comes later | *The renderer does not create the map. The renderer reveals a map that already exists as a deterministic spatial state.* What is drawn may be far richer than what is authoritative |
| tactical compilation | a brief of intent (routes, layers, approaches, protected spawns, lane lengths), and the question whether a geometry satisfying it can be built |
| mutation | plant geometric defects (a route removed, a spawn moved, a sightline opened) and require that a registered court catches each |
| the network | derived from the same world. Not lockstep: a server that is the authority, deterministic collision and visibility, quantized state, a replayable simulation |
| the certificate | evidence about one immutable map state: `MapHash → Certificate`, never the reverse |

**Considered against the tree.** Each line is what the ledger or the code already says. None is a proposal.

| the text asks for | what stands |
|---|---|
| a new source language, *immediately, in DIFF-0* (the proposal's roadmap) | DESIGN-IR/DIFF-0 is closed by the owner's own word (*stop adding architecture here*). A new statement kind is a new language and a new registration, and the meaning court registered behind the compiler (HERMENEUTICS-0) reads the language first |
| spawns and objectives | identities that outlive admission. The world holds cells and five classes; once admitted, nothing names a room. Persistent objects are a court he deferred by name |
| courts of constraints | constraints are a court he deferred by name. The design tool's *readings* (what is reachable from the camera) are views and are not certified. The text gives those two deferred courts their content |
| boxes, planes and height | the picture's trust root is a frozen oracle for a lattice of cells. A new kind of geometry needs a reference to hold the kernel to, as the bearing camera needed its second tag |
| integers only | the tree's already: the tick law, the bearing camera, the fold |
| rays the same on every platform | one ray law exists and is held to the oracle on both machines by rows of the gate |
| movement between cells | the world stays discrete. HOLD-WALK-0 records that this is not the free movement he wants |
| a second player, a shot, a wire | none exists. A session has one camera |
| lockstep, or an authoritative server | neither exists. What exists is one sealed, append-only log of typed events, replayed to a head; replay is the authority |
| travel times, *two frames*, kill probability from samples | no time, no frame rate and no latency are claimed anywhere in the tree. A tick is the tree's unit |
| a map's own amendment chain; never edit a shipped map | a session is never modified: an admission makes a child. Every admitted event carries the id of the design that made it |
| a digest signed for a tournament | a seal here is a hash, not a signature (G16). The tree holds no key and no trust root |
| geometric mutants against courts | the method stands: defects planted one at a time, survivors named by class, never a score |
| human play as a separate measurement | the tree's grades already keep MEASURED apart from ESTABLISHED, and it adds no scalar |

**Two outside pages, found by search.** Paraphrased and attributed; nothing rests on them.

- *Visibility graph analysis.* The encyclopedia page on it: a way of analysing which parts of a plan's open space
  see which, introduced by Turner and colleagues in 2001 out of space syntax; their paper's title says it starts
  from the isovist. A visibility graph over open space is prior art. It would be carried here, not discovered.
- *A level-design tutorial for Counter-Strike layouts* (worldofleveldesign.com): two or three main paths from the
  attackers' spawn, each ending in a choke point; the time each team takes to reach a choke is measured and the
  layout adjusted until the times are close, the defenders a little early; maps are judged by playing both sides.
  So the practice the text wants to make executable already measures timings, by hand and by play.

**Where he places it (a later text, the same day).** Not in this rung: *I would not let the arena material
contaminate this rung.* The order he draws: the compiler's rung; then *harden observation semantics*, which is the
correction of a row that read the clock (G30); then independent reconstruction on the host; then a spatial
representation; collision, visibility and navigation derived from geometry; courts of competitive constraints; a
playable arena. His reason for the order: *before Verðandi starts certifying spatial claims, the court machinery
itself has to be trustworthy about what it observes.*

**What stays declared.** All of it. Whether this becomes a rung, and where it sits against LIVE-AI-EDIT-0, a
graphical editor, objects and constraints, is the owner's to rule.

**Grade.** DECLARED: the text. OBSERVED: nothing; no arena was drawn and nothing was computed.
**does_not_show.** That any of it can be built over a frozen oracle of cells. That a constraint which passes makes
a map good to play. That two machines would agree on a match.

### Self-optimizing code, and its correction to a layout court · **declared** (two texts the owner brought, 2026-10-04); considered at his word; not registered, nothing built
Two texts, brought one after the other, and a review between them. Neither names its author, and both speak of the
owner in the third person. Nothing here is registered, nothing is built, and the order of the route is unchanged.

**The first text: *Microarchitectural Polymorphic Compilation (Self-Optimizing Immutable Code)*.** It starts from the
Epistemic Invariance theorem and LOCALITY-0, and proposes a compiler toolchain that takes the rendering kernel and
"continuously, dynamically mutates its memory layout, thread partitioning, and assembly instruction selection while
running live production workloads". Its argument: because byte identity is a hard landing condition, thousands of
such experiments can be tried safely under process isolation; a mutation that moves a single bit turns the gate
red and is discarded; one that passes the byte-identity court and lowers latency is adopted by the machine itself.
It says this moves optimization "away from human guesswork", and that the result is a permanently mutating
substrate "completely invisible to memory-scraping cheat engines".

**The owner's words.** *i think you should pause for this tool for this repo.* Asked in court what the pause meant
for the route, he answered: *consider:*. On the form it would take if it were ever taken up, and on how its
anti-cheat sentence should be recorded, he stated no preference. The review's reading is therefore recorded for
both, as a reading and not as a ruling.

**The review, as considered.** One thing fits and seven collide.

- **What fits.** The tree already does a small version of this by hand. LOCALITY-0 built its layouts as separate
  monomorphized binaries, held each byte-identical on the gate, timed them process-isolated and interleaved on the
  host, and adopted one by a rule locked before the number, keeping the loser on the record. GAUNTLET-2's thread
  sweep and BEARING-FAST-0's treads are the same shape. Enumerating a registered, finite space of such variants and
  running that court for each is the existing method, mechanized.
- **1. Live measurement contradicts the theorem it cites.** Epistemic Invariance says a layout's cost can be
  extracted only while the execution boundary is held static: monomorphize, process-isolate, interleave. A live
  loop taking a person's input is the opposite condition.
- **2. A program that changes itself at content time is a program the gate did not certify.** The gate certifies
  the machine; content time never runs it. Every saved session names the renderer it was made with, by the sha256
  of the render sources. A binary that mutates has no such name.
- **3. Automatic adoption meets `built ≠ adopted`, and the noise on record.** The same court has run 40–60% slower
  on another run the same day (G13), and labels have flipped on three samples (G10). LOCALITY-0's adopted gain was
  about 1.07×. Taking the best of thousands of trials at that noise selects the noise.
- **4. Byte identity over a court set is evidence about that set.** A layout that is a bijection is also right by
  construction, and a row checks the bijection. A mutated instruction sequence has no such backing.
- **5. Generating or rewriting code at run time is not std-only.**
- **6. The ruling of 2026-10-01.** The next work is chosen by what evidence is worth buying. The staircase reopens
  only if a court misses its target, and layout and cache experiments are on that list as deferred, with no gain
  claimed. The live loop's timing is not measured at all (G21).
- **7. The security sentence has nothing under it.** This repository has no threat model and claims nothing about
  an adversary. What a cheat reads is state, and the saved form keeps the world's state open and replayable on
  purpose.

**The second text.** It accepts the review point by point and offers a correction it calls a *Static Layout
Synthesis Gate (SYNTH-LAYOUT-0)*, which is a declared name and not seated. Its three terms: it runs at compile
time, as a pre-build step under `verify/`; it enumerates only structural data-layout variants and never mutates
instructions, runs the interleaved courts, selects by a rule locked beforehand and bakes one static layout into the
binary; and the winner carries a permanent content-addressed identity, so every session it makes names a fixed
source hash. Nothing mutates at run time. On the security sentence it agrees with the review: the world's state is
open by design, and diversity gives probabilistic mitigation of control-flow hijacking, not protection against
reading data.

**Where the correction still meets rules in force.** It is close. Six things in it are not this tree's.

- **The gate does not time anything.** The correction puts the interleaved timing and the selection inside the
  development gate. Here correctness is on the gate and speed is off it: no row reads a wall-clock number, and two
  passes must be byte-identical on any machine. A gate that timed variants would give a different answer on every
  host and on every run. What the gate can hold is that each variant is byte-identical and that the adopted one is
  the one in the source. Timing is a host court with a sealer, as LOCALITY-0's was.
- **A build does not choose the renderer.** If a pre-build step picked the winner, two hosts could build two
  renderers from one tree, and a session's renderer identity would stop naming one program. Here the choice is
  made once, on a named host, sealed as a record, and then committed as source by the owner's lock. The identity
  follows from the committed source and needs no new stamp.
- **"Selects the optimal" needs the same care as any adoption.** A margin declared beforehand, a confirming run on
  fresh samples, the losers kept on the record, and the space small enough that the best of it is not just the
  luckiest. ALLOC-REUSE-1's court is the model.
- **The court set is not "the standard twenty witnesses".** Those are Urðr's, from the placement that preceded
  this repository. Here a fast path is held to the corpus (six scenes, two tile sets) and the gate's adversarial
  cameras, 19 cases for the facing emit, and the bearing camera has its own court set.
- **Three of its terms are not in this tree.** `conventions.py`, an "Arbitrary-Boundary Law" and "Temporal Fidelity
  Accounting" appear nowhere in Verðandi. They are recorded as the text's own terms and were not opened here. What
  this tree has in their place is a registered entry that keeps its rejected alternatives (Morton, in LOCALITY-0)
  and the ruling of 2026-10-01. Likewise there are no crates and no build macros here: a variant is a
  monomorphization inside `kernel/fast.rs`, as the two layouts already are.
- **Two readings of the evidence are stronger than the evidence.** FRAME-SPLIT-0 is not unmeasured: it was measured
  twice, for the modelled loop; what is unmeasured is the live loop. And the outside sources are reported below in
  their own terms: one found a bias, in its own benchmarks; neither proved a law.

And one thing the correction does not change: it is still an optimization of the kernel. Being lawful does not make
it next. By the ruling of 2026-10-01 it waits behind the measurement of the live loop, and it reopens when a court
misses a target.

**Outside sources (attributed; hypotheses, not claims of this repository).** Curtsinger and Berger's Stabilizer
treats one binary as a single sample from the space of memory layouts, re-randomizes the layout during a run so
that layout effects can be tested statistically, and reports that across its benchmark suite the difference
between two compiler optimization levels could not be told from layout noise. Mytkowicz and others report that
details of an experimental setup that look harmless can bias a performance measurement enough to reverse a
conclusion, and recommend randomizing the setup. Schkufza and others' stochastic superoptimizer searches with test
cases and accepts a rewrite only after a formal equivalence check, on loop-free code. Larsen and others'
systematization of software diversity describes its protection as probabilistic and lists disclosure of the
diversified implementation as an open problem. Read here in the first paper, in the authors' summary page, in
Adrian Colyer's summary, and in the authors' publication page.

**Grade.** DECLARED: both texts, and the name. OBSERVED: nothing; no variant was built and nothing was timed.
**does_not_show.** That a wider layout space holds any gain on this host: LOCALITY-0 measured two layouts, and its
gain was small beside the drift between runs. That any of this would matter to the live editor, whose timing is
unmeasured. Anything about security. **What stands.** The order is unchanged: READER-COURT-0's build is next. If a
layout court is ever taken up it is courted and registered like any rung, and the review's reading of its form
(offline, a small registered space, byte identity on the gate, timing on the host, adoption by the owner's lock)
is a reading and has not been ruled.

**On the host (DANIELDILLBERG).** This record was applied, the gate passed with it (GATE PASSED, rowset
`0b423b279a40c85c`, 218 rows, 0 fail, 0 skipped) and it was pushed, `25b5c17..b847810`. The owner's word after it:
*take the next.* The next, by the order that stands, is READER-COURT-0's build.

### GAME-0 — Urðr's game layer as frozen evidence · **landed**
The seventeen discrete game-layer slices (`gamegen` … `cue`), their corpora, suites, briefs and the D24/D25 boundaries,
carried verbatim from `urdr-oracle-1` into `oracle/game/`, each file listed with its sha256 and Urðr git blob id, and
Urðr's own suites passing in place (`game-frozen`, `game-suites`, `game-plant`, `game-not-runtime`). Evidence, not a
runtime dependency: the kernel, workshop and shell do not read it. **ORACLE-D0 (landed):** the same carried code,
in place, recomputes the oracle's third hash `D_0` from the oracle's view on every gate (`oracle-d0`, with a plant),
so all three oracle hashes are now checked; the studio still mints none of `D_0`.

### SKYBOX-0 / PHYSICS-0 — the skybox beyond the oracle; physics already in the tag
The skybox stays *beyond* the frozen oracle and is gated behind the new-semantics route (`SEMANTIC-0`'s machinery):
named, courted, and not seated until that route exists. Physics is not in the same position. An earlier version of
this roadmap said it was beyond the oracle, and that was wrong. `urdr-oracle-1` carries Urðr's exact ℤ/ℚ mechanics
(rungs 1–4), its bounded Q32.32 real-time path (rung 5) and its lockstep/rollback netcode, all as earned CORE
semantics with frozen corpora. They reach the studio by the `GAME-0` route, and only physics the tag does not carry
needs the new-semantics route.

### IMPOSSIBILITY-0 — measured negative results as level preconditions
Some world states are *provably unreachable*; recording those impossibilities as level preconditions is itself a
form of authored semantics, and a natural companion to `SEMANTIC-0`.

---

## The invariants that carry forward

Everything above obeys the same discipline that carried the render campaign:

- **Earn the authority.** CORE semantics come only from Urðr: carried verbatim from the tag already cited (as
  `GAME-0` carries the game layer), or earned there and re-frozen under a new name. New VIEW semantics may be
  Verðandi-local but must be pinned by rows here. The shell never mints truth.
- **Byte-identity where an oracle exists; a pinned reference where one does not.** A rung with a frozen oracle proves
  byte-identity against it; a rung inventing new semantics defines a reference and pins it, then defends *that*.
- **The model may propose; only the verifier may admit** (declared, LLM-BUILDER-0). Anything that suggests a change —
  a key, a mouse, a script, one day a model — reaches the world only as a typed event the session validates and
  replays. Verðandi does not execute what a proposer writes; it records what the verifier admits.
- **The gate certifies the program; content is admitted, not gated** (declared, 2026-10-03). The engineering gate
  runs when the program changes. Content, which today means a session's events, is admitted by checks on the
  artifact itself and never invokes the gate. A change to the laws content runs under is a program change.
- **Preregister the method before the number,** including the failure condition and the null. Measure before
  optimize; re-measure after. Correctness on the gate, speed off it. The record stores numbers; the reading
  interprets.

The render half proved this discipline scales to a hard optimization campaign. The authoring half is where it meets
its more interesting test: proving that a *living, editable world* can be as honestly evidenced as a static picture.

---

## Sources (prior art the named rungs draw on)

- [DXGI flip model — DirectX Developer Blog](https://devblogs.microsoft.com/directx/dxgi-flip-model/) and
  [Reduce latency with DXGI 1.3 swap chains — Microsoft Learn](https://learn.microsoft.com/en-us/windows/uwp/gaming/reduce-latency-with-dxgi-1-3-swap-chains) (PRESENT-1)
- [Multithreaded software rasterizer — Zach Bethel](https://zachbethel.wordpress.com/2012/11/28/multithreaded-software-rasterizer/) and
  [Thread pool — Wikipedia](https://en.wikipedia.org/wiki/Thread_pool) (execution refinements; see [`GHOSTS.md`](GHOSTS.md) G1/G3)
- [Roofline: an insightful visual performance model — CACM](https://cacm.acm.org/research/roofline-an-insightful-visual-performance-model-for-multicore-architectures/) and
  [Roofline Performance Model — NERSC](https://docs.nersc.gov/tools/performance/roofline/) (the T=8 bandwidth question; see [`GHOSTS.md`](GHOSTS.md) G2)
- [Working with authoring and runtime data — Unity Entities](https://docs.unity3d.com/Packages/com.unity.entities@1.0/manual/editor-authoring-runtime.html) (interactive capture; the authoring/runtime split)
- [Conflict-free replicated data type — Wikipedia](https://en.wikipedia.org/wiki/Conflict-free_replicated_data_type) and
  [Delta-state replicated data types (Almeida et al.)](https://members.loria.fr/CIgnat/files/replication/Delta-CRDT.pdf) (MERGE-0's convergence theory)
- [Scoped threads (`std::thread::scope`) — Rust](https://doc.rust-lang.org/std/thread/fn.scope.html) (structured concurrency; see [`GHOSTS.md`](GHOSTS.md) G1)
- ADMIT-0 (outside sources, attributed; hypotheses, not claims of this repository):
  [LangSec explained in a few slogans](https://sergey.cs.dartmouth.edu/langsec/occupy/),
  [JSON interoperability vulnerabilities — Bishop Fox](https://bishopfox.com/blog/json-interoperability-vulnerabilities),
  [RFC 8259](https://www.rfc-editor.org/rfc/rfc8259.txt),
  [RFC 8785 (JCS)](https://www.rfc-editor.org/rfc/rfc8785.html),
  [Canonicalization Failures as a Recurring Vulnerability Class (Brömme)](https://arxiv.org/abs/2608.06508),
  ["YOLO" is not a valid hash construction — Trail of Bits](https://blog.trailofbits.com/2024/08/21/yolo-is-not-a-valid-hash-construction/),
  Design Patterns for Securing LLM Agents against Prompt Injections (arXiv 2506.08837) and CaMeL: Defeating Prompt
  Injections by Design (arXiv 2503.18813), both read in Simon Willison's summaries
  ([patterns](https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/),
  [CaMeL](https://simonwillison.net/2025/apr/11/camel/)),
  [The kernel and the De Bruijn criterion](https://bnaskrecki.faculty.wmi.amu.edu.pl/vietnam2026/book/peano/kernel.html),
  [JSONSchemaBench](https://arxiv.org/html/2501.10868v2),
  [Finding Consensus Bugs in Ethereum via Multi-transaction Differential Fuzzing (Fluffy, OSDI '21)](https://www.usenix.org/conference/osdi21/presentation/yang),
  [Appending events — EventStoreDB](https://docs.kurrent.io/clients/tcp/dotnet/21.2/appending.html),
  [Essential features of an Event Store](https://eventsandstuff.substack.com/p/essential-features-of-an-event-store),
  [All File Systems Are Not Created Equal (ALICE, OSDI '14)](https://cs.uwaterloo.ca/~alkiswan/papers/alice-osdi14.pdf),
  [MoveFileExA — Microsoft Learn](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-movefileexa),
  [ReplaceFileW — Microsoft Learn](https://learn.microsoft.com/windows/win32/api/winbase/nf-winbase-replacefilew),
  [Constraint Is All You Need (Xu et al.)](https://www.pcgworkshop.com/archive/xu2025constraint.pdf),
  [Agentic PCG](https://zehua-jiang.github.io/AgenticPCG/),
  [About Raw Input — Microsoft Learn](https://learn.microsoft.com/en-au/windows/win32/inputdev/about-raw-input).
  For the self-optimizing-code texts (outside sources, attributed):
  [Stabilizer: Statistically Sound Performance Evaluation (Curtsinger and Berger)](https://people.cs.umass.edu/~emery/pubs/stabilizer-asplos13.pdf),
  [Producing Wrong Data Without Doing Anything Obviously Wrong! (Mytkowicz et al.)](https://sape.inf.usi.ch/publications/asplos09.html),
  [Stochastic program optimization (Schkufza et al.), in Adrian Colyer's summary](https://blog.acolyer.org/2017/03/30/stochastic-program-optimization/),
  [SoK: Automated Software Diversity (Larsen et al.)](https://ics.uci.edu/~perl/publication/diversity_sok).
  The review's own citations, not opened here: the LangSec workshop page, SLSA provenance v1.2 and OWASP's AI Agent
  Security cheat sheet.
