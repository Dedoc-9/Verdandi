<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!-- Copyright (C) 2026 Daniel J. Dillberg -->

# Roadmap — toward a live, authorable world

*Where the program stands, what "a live authorable world" means for it, and the sequenced, falsifiable path to get
there. This roadmap names rungs that are already public in [`verify/RUNGS.md`](../verify/RUNGS.md), and — since the
owner published it — the route to walking in a live, authorable world, whose rungs were named before they were built (most are built now). The
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

And everything the tree's registered writers save and read back is now one bounded language with one verdict from
every reader (`READER-COURT-0`, built; the gate passes on the host, 226 rows, and is pushed). The refusal log, the run
ledger and the files of `design/` and `graybox/` are plain JSON outside it.

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
design tool and the admission (`DESIGN-IR/DIFF-0`, `2baa42f3`, five rows). Behind it, built at his word: the meaning
of the design language as the owner's own rulings, literal targets and laws, which neither program computes, and to
which both are held (`HERMENEUTICS-0`, `22d52d02`, four rows, under his amendment `HERMENEUTICS-0a`). The gate is 251
rows and passes here and on the host, FULL×2 there by the witness, and is pushed. Then, by his ruling of 2026-10-09,
the gate stops growing: it is a release instrument, and the daily objective is a playable first-person graybox
(`FPS-GRAYBOX-0`, below).

What is *not* yet done: design objects that outlive admission, constraints, and a model at the seam
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
HERMENEUTICS-0   named by the owner (2026-10-07) for the gap DESIGN-IR/DIFF-0's own amendment states: the meaning of the design language, apart from either program that compiles it. The concept locked, its build deferred until after DIFF-0, folding it into DIFF-0 rejected. Semiotics, one level earlier, is a vocabulary audit and not a rung, declared. His court the same day: one reading ratified, six cases locked, four laws ratified as theorems, a corpus of ten designs with literal targets — registered (`22d52d02`) and pushed (`5c8ad19..11afebf`); not built; built after DIFF-0 is built, courted and FULL×2; PROCEED, his word (2026-10-09); read for the build, two rules of DESIGN-IR/DIFF-0's rows stood in the way of its registered instrument, and he ruled (A): HERMENEUTICS-0a widens each by the least — the eleven plants first, the three the shell lacks after them, `first-wins` and `entrance-dropped` given twins in the reference; the reference's users DIFF-0's rows and these four — with REASON-COURT-0d for the moved pin; BUILT (2026-10-09) under HERMENEUTICS-0a and REASON-COURT-0d: four rows, 251 in the gate; both programs give each registered outcome on the registered parent, the four laws hold on their instances, and the five plants, planted alike so that a comparison of the programs is blind, are each caught by a case or a law — and by DIFF-0's own registered values, all five, as the entry expected; on the host FULL×2 by the witness, pushed (`b386b85..3dc15ec`); then frozen
      ↓
FPS-GRAYBOX-0    the owner's sprint (2026-10-09): stop expanding the gate; a playable first-person graybox on the canonical level — a tactical layout with three routes, cover, spawns and an objective; mouse look, WASD, jump, collision, a weapon placeholder; one weapon, hits, target feedback, reset. The design compiler keeps the layout; the smallest runtime layer carries height, collision and play. His amendment: the conversion certified, not the mesh — a canonical world from which collision and the render mesh are derived, a manifest, independent conformance checks and defect-directed mutations, a smoke suite, replay determinism on one platform; boundaries in docs/BOUNDARIES.md. The full gate at release checkpoints only; BUILT the same day, beside the certified tree: `python graybox/serve.py` — the tactical map's walls and floor admitted through the design tool, an overlay for the rest, three routes walked by a bot through the real movement, seven planted conversion defects refused
      ↓
FPS-VISUAL-0     the owner's visual pass (2026-10-09), outside the gate: a sky and a sun, floor materials (the 1 m grid a hidden debug mode), wall panels and trim, varied cover, one weapon model whose transform stays apart from the shot; movement, collision, source hashes and replay kept; screenshots and timings before and after, and no improvement claimed unmeasured. His rule: the canonical world says what the map means, the collision world what blocks, the render world how it looks, and the render world decides nothing that blocks; BUILT the same day: a sky and a traced sun, floor modules, panelled walls, dressed cover, a 22-part weapon apart from the shot; the first renderer kept beside it; a self-test that holds the drawn solids to the collision world face by face and keeps decoration out of play, seven planted renderer defects refused; timed in SwiftShader, then on the host (0179: the lit renderer's median draw and readback 1.36–1.53 times the first's)
      ↓
ART-GENERATION-0 the owner's pivot (2026-10-10), ahead of EVIDENCE-LINK-0: verification serves the art; prompt to playable art at AAA ambition, Unreal 5.8 to render it, Verðandi keeping layout, collision and lineage. Its first slice built beside the certified tree (`art/`): one brief dressed onto the tactical graybox, its checks, a look and a layout revision; the Unreal import written, not yet run on an engine
      ↓
DIRECTOR-0       the owner's ruling (2026-10-10): the operator loop for prompted art — candidates checked against the head they meet, admitted or refused by a person, every step in an append-only ledger; a canonical form and conformance vectors a second implementation reproduces (built beside the tree: art/director.py, art/director/; a std-only Rust second implementation reproduces all 62 vectors)
      ↓
NATIVE-PLAZA-0   the owner's rulings (2026-10-10, 2026-10-11): Verðandi-native the primary architecture, Unreal 5.8 a secondary path; the plaza played in the browser through an art-owned launcher (art/play.py) and a WebGL 2 renderer, the graybox's simulation moving against C; two rounds evaluated, not yet chosen; live edits (2026-10-11): an edit to the brief or to a candidate intent drawn in the running page, the game untouched, a refused edit leaving the scene before it
      ↓
DET-MATH-0       the owner's ruling (2026-10-11), outside the gate: the simulation's rules made portable. Every function whose last bits the language leaves to the engine and that reached the authoritative state (sin, cos, hypot, atan2) replaced by fdlibm's algorithms and exact square roots, built from operations ECMA-262 fixes; the rules versioned (1), rules 0 kept as the baseline; held by rules-arithmetic and math-fence in the self-test and by graybox/rules_ref.py; the same bits measured in two V8 engines and CPython; ACCEPTED by the owner (2026-10-11), cross-browser equivalence NOT ESTABLISHED until Firefox and Chromium are compared on one machine; compared on his machine the same day: Firefox 157 and Edge 155 on the same recorded inputs, every rules-1 snapshot the same at every tick of the tactical map's three runs; by his ruling of the same day, cross-browser equivalence on the tactical map advanced from NOT ESTABLISHED to MEASURED once
      ↓
TICK-REF-0       the owner's ruling (2026-10-11), "NEXT": a second, independent implementation of the full tick, in Python, from a written specification (graybox/RULES-1.md), verifying a browser's trace tick by tick and naming the first differing field; the same bytes as Chromium 141 and node 22 at every tick of both maps' runs, and as Firefox 157's and Edge 155's on his machine (the tactical map, each verified directly); accepted provisionally by the owner (2026-10-11); outside the gate
      ↓
BOT-REF-0        the owner's ruling (2026-10-11), "the next vertical slice": the walk made in Python from the map alone, by a policy written down (graybox/WALK-1.md, walk-1) and advanced by tick_ref.py (graybox/bot_ref.py), so that no browser originates the reference walk; on the tactical map its start and 1,787 inputs the same bytes as the browsers' own bot's, and Chromium 141, node 22, and on his machine Firefox 157 and Edge 155, playing them reach the Python tick's state at every tick; ACCEPTED provisionally by the owner (2026-10-11); the witness level next; outside the gate
      ↓
INPUT-CONTRACT-0 the owner's ruling (2026-10-11): the tick's input admitted or refused, whole, before anything is touched — a written domain (RULES-1.md, The input), one category for each fault, a shared table of 70 hostile and admitted cases (graybox/web/input_cases.json); sim.js and tick_ref.py agree on every step, outcome and state, in node 22 and Chromium 141, and on his machine in Firefox 157 and Edge 155; nothing admitted changed; outside the gate
      ↓
STUDIO-0         the owner's direction and ruling (2026-10-11): a director summoned into the running plaza — E selects, Enter summons, a prompt answered by at most three candidates drawn in place with the game untouched, admit, reject and undo through the director's ledger; "the model proposes changes—it never directly mutates the live world"; a gateway (art/studio.py) between the page and a provider command (a scripted provider; Claude through the Anthropic Messages API), its contract in art/STUDIO.md; his acceptance test met in Chromium 141 in the build container; on his machine (Windows) its self-test 29 / 29, and the scripted provider tried from the page; outside the gate
      ↓
STUDIO-1         the owner's rulings (2026-10-11), after trying STUDIO-0: two real model paths, "Both, CLI first" (Claude Code's CLI as a provider, the Anthropic API kept), compared on the same prompts; and references — visible tags, a target and up to four pinned pieces, their geometry in metres and the relations between them measured, each reference bound to a piece and a scene revision and never silently redirected; no new art vocabulary in this slice (an image of the view next, connecting pieces after); the CLI provider built, and a real model reached through it in the build container (its probe SHOWN); the references built: tags E and R make, bound to an object's id and never moved, the request's geometry and relations measured from the scene's boxes, and what each candidate touches; a real model, asked four prompts about three tagged canopies, changed exactly the objects each prompt named in 15 of 15 candidates; on his machine, through Claude Code on his Claude plan (claude-opus-5-5), the same in all 23 candidates the director drew, and in the page a canopy matched to another by its tag and admitted; outside the gate
      ↓
STUDIO-APP-0     the owner's direction (2026-10-12): "The next objective should be a runnable Verðandi Studio, not another narrowly scoped rung" — a desktop icon, a live world with the director, a studio that proposes, builds, tests and offers changes to itself, promoted by explicit admission with rollback, "Keep the studio that is running separate from the studio being built"; researched and planned in docs/STUDIO-APP.md (the architecture decision: the page in Edge's application mode under a std-only stub and a std-lib supervisor; VCT-0, one change transaction with domain validators, ACCT among its parents; five batches); its interfaces and transaction frozen in docs/STUDIO-CONTRACT.md (the commit point the durable blessed record; Recover(J, P, F) in sixteen rules, its reference art/studio_txn.py checked over every enumerated crash point); B1's first part built (crash-safe admissions, tags kept and shown, the API provider on structured outputs with Opus 5.5, play.py's health and shutdown, the five probes); outside the gate
      ↓
EVIDENCE-LINK-0  accepted by the owner (2026-10-09) as the next qualifying slice: each claim a commit message or a document copies about a recorded event — ids, push ranges, row counts, hashes, prediction outcomes — traced to its authoritative source, never only to another copy; an instrument outside the repository that reads and reports; declared, defined and registered after HERMENEUTICS-0 is advanced and not bundled into it; by his final ruling of the same day, the next verification pivot
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

### HOST-STATE-1 — the reported clock and paging · **landed** (`b992d9dd`); first host look taken; recorded beside each run of DRIFT-0's sitting 1
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
`LATENCY-0` *established* only that the composed-GDI present is coupled to the refresh: frame-ready to composited
waits for the next DWM composition, a wait bounded by the refresh period (p50 5,921 µs against a 13,298 µs refresh on
the host). An earlier wording here read that bound as a floor; corrected by the owner's ruling (2026-10-09). `PRESENT-1`'s
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

### The design language — one design authority, many editors · **declared** (the owner's, 2026-10-03); its objects and constraints not registered and not built; a cell-level design text and its certified compiler built since (DESIGN-IR/DIFF-0)
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

### Hermeneutics and semiotics — what the design language means, apart from what compiles it · hermeneutics **built** (`22d52d02`, under its amendment `7e012752`; four rows, 251 in the gate; FULL×2 on the host; pushed), semiotics **declared** (texts the owner brought, 2026-10-07), not built
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

### FPS-GRAYBOX-0 — the playable slice · **the sprint** (the owner's ruling, 2026-10-09); the gate stops growing · **built**: the slice runs (`graybox/`)

**His ruling.** *Stop expanding the gate.* More verification architecture had come to compete with the product he
wants: a design tool that compiles a reachable top-down grid is map data, and not yet a playable 3D FPS. The next
milestone crosses that boundary. HERMENEUTICS-0 is closed once on the host and then frozen; no newly found hardening
becomes a prerequisite for gameplay. The reach map is worth keeping and is not built now.

**The four findings**, recorded for later repair and not claimed fixed:

| finding | his ruling |
|---|---|
| `reasoncourt-source` reads a citation's line number and does not check it | a real source-validation defect; repair deferred (G34) |
| `records-preregistered` skips a record that cites no registration | a real registration-coverage defect; repair deferred (G35) |
| this roadmap misstated LATENCY-0's bound | corrected in the next documentation batch (this one; PRESENT-1, above) |
| the witness misses changes hidden by Git's flags and settings | a real witness limitation; its empty status alone is not proof of a clean checkout (G36) |

**When to run what**, his rule from now on:

| what changed | what runs |
|---|---|
| the compiler, or authoritative semantics | the relevant engineering checks |
| map content only | compile the level; light geometry and connectivity checks |
| renderer or gameplay code | the relevant runtime tests |
| a registered release checkpoint, or a change that threatens the certified contract | the full gate |

Not after every room or corridor edit.

**The milestone.** Three parts: a tactical graybox — three connected routes, distinct central and side engagements,
cover, spawn regions, objective locations, simple geometry before art; playable first person — mouse look, WASD,
jump, collision, a camera, a visible weapon placeholder, a player who actually traverses the level; a combat loop —
one weapon, firing, hit detection, target feedback, a respawn or reset. His caveat: if the design tool cannot express
height, collision volumes or traversal, do not force them into its tile grammar; the design compiler keeps the map's
canonical layout and the smallest separate runtime representation carries the rest.

**His stop rule**, in brief: one short inspection pass, then the first running scene; load the level from an explicit,
deterministic representation; real 3D walls, floors, openings and cover; collision and gravity; a documented launch
command; a smoke test. Not D3D12, upscaling, networking, anti-cheat, elaborate art, a general rendering abstraction,
proof composition or a new gate framework. No registered law changed to make gameplay work, and no new rung unless a
concrete defect blocks the slice. *Deliver a playable graybox, not another roadmap.* After it: map geometry, combat,
performance measured with valid boundaries, 720p / 1080p / 1440p, networking.

**His amendment: boundary integrity and runtime conformance.** He accepted five proposals in narrowed form:

| proposal | his ruling |
|---|---|
| conversion-layer provenance | accept, strengthened: bind the built level to its source and converter, and check the gameplay geometry independently. *A hash alone proves identity, not correctness* |
| cross-platform physics determinism | accept the principle, narrow the claim: replay determinism on one platform first; across platforms only if the numeric and physics contracts promise it |
| unsafe-code boundaries | accept: declare the trusted core, the runtime shell and the interface; review when a boundary changes |
| automated smoke tests | accept, staged: load, spawn, collision, clean exit now; performance thresholds when a stable renderer and test machine exist |
| input-latency instrumentation on day one | accept the instrumentation, defer any absolute claim: each segment recorded apart, and summed software timings never called input-to-photon |

Its core: *certify the conversion, not the mesh.* A verified design passes through several representations, so
declare which one owns gameplay truth — a canonical spatial representation from which the collision world and the
render mesh are each derived, the renderer never the authority for collision. Each built level gets a manifest (its
source, its converter, the canonical and collision representations' hashes, semantic identifiers back to the source)
and independent conformance checks (spawns valid and traversable, openings open, walls blocking at named probes, no
undeclared obstruction on a required route, provenance kept), shown to bite by defect-directed mutations: an opening
collapsed, a spawn moved into a wall, an invisible blocker. *Unsafe code is not automatically a contract violation;
unbounded authority across the boundary is.* Cross-platform bit-exact determinism and absolute input-to-photon latency
stay separate claims until their contracts and measurement protocols exist. *Do not expand the certification
framework beyond the concrete properties needed to establish the first playable vertical slice.*

**Grade.** DECLARED: his rulings and his amendment.

**Built (2026-10-09): the slice runs.** `python graybox/serve.py` opens a first-person graybox in the browser; the
folder's README says how to play and test it.

```text
  tactical.design ──design tool──► shell design-compile ──► shell design ──► tactical.layout    walls and floor
  tactical.gbx (height, cover, spawns, objective, targets, probes, routes) ──────────┤
                                                                                     ▼
                         level.py:  D ──► W canonical world ──► C collision world ──► sim.js (moves against C)
                                             └──────────────────────────────────────► render.js (draws W)
```

| his acceptance criterion | what stands |
|---|---|
| launches into a 3D first-person scene | WebGL in the browser, served by a standard-library Python script on 127.0.0.1 |
| mouse look and WASD | pointer lock; a fixed tick of 1/120 s, input taken as one record a tick |
| collision prevents passage through solid geometry | the player, a circle of 0.35 m, against each cell's solid top; a step of at most 0.55 m; the standing targets solid |
| a complete route through the graybox | the tactical map's three routes, base A to base B, each walked end to end by a bot through the real movement |
| the level from explicit source data | the walls and floor are the layout the design tool admitted (head `c862f3b1…`), read back with its heads; the overlay is a text file; nothing is drawn that the converter did not produce |
| launch and controls documented | `graybox/README.md` |
| a smoke test | `python graybox/check.py` for map content, and `python graybox/serve.py tactical --selftest` for the runtime |

**The exact limitation that made a separate layer.** VERDANDI-DESIGN 0 says, of a 2D grid, which cells are rock and
which floor, and the colour of five classes. It has no height, no volume, no collision rule and no gameplay mark. So,
by his caveat, the language is not stretched: the design tool keeps the tactical map's walls and floor (an
admitted design of 25 statements, 610 operations, every one of its 736 floor cells reachable), and a separate overlay
says the rest, on floor cells only. The witness level plays too, read from its pinned bytes.

**Why a browser.** No package could be fetched where it was built (the egress policy refuses the package index), and
the owner's machine has Python and a browser. So the runtime needs Python's standard library and WebGL and nothing
else. The simulation, `sim.js`, holds no DOM and runs under node as well; the renderer is one file behind one call,
and can be replaced without touching the simulation or the maps.

**His amendment, where it stands.** The canonical world W owns gameplay truth; the collision world C is derived from
it and is all the simulation moves against; the renderer draws W and is never asked whether a wall is there. Each
map's manifest names its source, the converter's hash, and W's and C's hashes, and every cell of W names the source
lines that made it. `check.py` is the independent verifier: it reads the source again with its own reader and holds
W and C to it with its own search — walls and floor, collision, provenance, spawns, probes, routes, the bases and the
objective connected, the routes distinct — and refuses seven planted defects: an opening collapsed by the converter,
the same in the source, a spawn moved into a wall, an invisible blocker on a route, a wall made passable in
collision, provenance stripped, and a spawn written into a wall in the map file (refused by the converter). The
runtime's own self-test: load, both spawns, every probe walked at, the three routes walked, gravity and the jump, a 1 m
block refused on foot and mounted with a jump, a hit in the open, a miss behind a wall, the target back up, reset, a
recorded route replayed twice with the state hashed at every tick, one frame drawn. The boundaries are in
[`docs/BOUNDARIES.md`](BOUNDARIES.md). The HUD shows the page's own software timings, each segment apart, and says
they are not input-to-photon.

**What is not there.** Other players and damage, an objective that scores, ammunition, sound, ramps, ceilings and
overhangs, interpolation between ticks. Nothing is claimed across browsers or machines, and no frame rate.

**Run here.** In the build container: the map checks, every check and mutation passing on both maps, and the tactical
layout compiled and admitted again through the design tool to the same head; the runtime's self-test 20 / 20 on the
tactical map and 17 / 17 on the witness level, in headless Chromium (SwiftShader WebGL) through `serve.py --selftest`,
which ended 0; walking with the keyboard, aiming and firing, captured in screenshots. On the owner's machine (with
FPS-VISUAL-0, below): the map checks and the self-test pass, and the mouse was not captured. The overlay took the
click; repaired by 0178.

**Grade.** OBSERVED (the build container): everything above. NOT_MEASURED: the slice on the owner's host, its frame
rate, and anything of feel. It is not a rung of the gate and adds no row.

**What an equal hash is worth (2026-10-10), at the owner's request.** He asked for it to be built, *"creative/pioneering"*,
*"consider mixing theorems"*. The replay compared hashes, and nothing showed that the hash read the whole state, or
that the state was all a tick reads. Four checks now say so, each with a plant it refuses:

- **`hash-coverage`.** The state's leaves are found by walking it. Each must be seen by the hash at its last bit,
  or be a leaf the world declares, equal to the world's value and of a kind no tick writes. FNV-1a always separates
  inputs that differ in one byte, and the last bit is one byte.
- **`fx-noninterference`.** The view's feedback, which the hash leaves out, never reaches the authoritative state.
  Twins are stepped in lockstep from reachable states.
- **`snapshot-resume`.** Bit-exact snapshots are resumed in fresh instances of the simulation, with the rules frozen.
- **`resume-realm`.** A snapshot is resumed in a worker, another realm, and a one-bit change must be told apart.

Together, equal replay hashes now mean an equal game in one browser, up to 32-bit collisions between states that
differ in more than one byte. The laws mixed are Reproducible Realization, Art/Gameplay Separation (the view's
feedback is the view's) and Creative Noninterference, each a property of pairs of runs (R-2). Seven defects were
planted by hand in a copy of `sim.js`, and each was refused by the check it targets. They were: the hash leaving out
`cooldown`, the targets' `downFor` or the side; a tick reading the hit marker; a count kept at module level; the
rules left unfrozen; and a new unhashed leaf.

With them comes a measurement, printed and never counted. Each run is played in counterfactual engines whose
`Math.sin`, `Math.cos` or `Math.hypot` is off by its last bit at every call. The state's bits parted, but no cell,
footing or hit changed ([`RESEARCH-FINDINGS.md`](RESEARCH-FINDINGS.md), R-6). The self-test is now 27 checks on the
tactical map and 24 on the witness level.

**Run here.** Headless Chromium: 27 / 27 three times and 24 / 24, line for line the same. Under node: the simulation's
22 and 19.

**On the owner's machine (2026-10-10).** 0187 applied as tree `ba6360f7…`, as predicted. The self-test passed 27 / 27
and 24 / 24 in the browser `serve.py` opened, every check's line as in the container, and the art checks passed. Pushed
`ef1e6ec..00b7645`. Four of the eight MEASURED lines differed from the container's. Every check matched, so the two
engines' `Math` returned different bits somewhere in these runs and rounding absorbed the difference
([`RESEARCH-FINDINGS.md`](RESEARCH-FINDINGS.md), R-6). OBSERVED, once.

**The trace experiment (2026-10-11), by the owner's ruling.** *"Investigate the cross-engine divergence, but do not
let that investigation become a prerequisite for the native plaza slice."* He asked for *"the runtime fingerprint,
actual transcendental input/output fingerprints, and first-divergence reporting in a small, separate experiment"*,
kept outside the certified gate.

- **What it is.** `graybox/trace.py` serves its own page and writes a trace: every call of `Math.sin`, `Math.cos`,
  `Math.hypot` and `Math.atan2` with its arguments' and result's bits, in call order, every tick's input and
  snapshot, and the browser's description of itself.
- **The comparison.** Each function's results are compared on common arguments, and the first differing call is
  classed as an argument or a result. The first differing input and state are reported, with the leaves.
- **Its own plants.** Five, each found where it was planted.

Node 22 and Chromium 141 differ by one ulp in `Math.sin` and `Math.cos` on a few arguments, and every tick of both
runs still matches (R-6). The self-test is unchanged, line for line.

**On the owner's machine (2026-10-11).** 0189 and 0190 applied as tree `aa7ddc63…`, as predicted; the director's ledger
verified at 21 events, the files at head `cac46b5c8e28`, the director's self-test and the art checks passed, the graybox self-test
27 / 27; `art\play.py plaza-night` launched; pushed `3eeab82..1b5e8f6`. His Firefox 157 trace against the container's
Chromium 141: `Math.hypot` different on 943 of 3,523 common arguments, `Math.sin` on 1 of 745, `Math.cos` and
`Math.atan2` the same, each difference one ulp; the first differing call the 2,386th, a result of `hypot`; every input
and state the same at every tick. OBSERVED once (R-6, with what it does not show and a remedy left to the owner).

### FPS-VISUAL-0 — the visual pass · **the owner's ruling** (2026-10-09); outside the certified gate · **built**: the graybox lit and dressed, the first renderer kept beside it

**His ruling.** The graybox plays; the next pass makes it look like a place, and the certified gate stays out of it.
His finite milestone:

1. A sky gradient and more convincing directional lighting.
2. Modular floor materials in place of the one-metre floor grid; the grid kept as a hidden debug mode.
3. Wall paneling, corner trim, and visually varied cover.
4. One real 3D viewmodel in place of the weapon block: receiver, barrel, sights, magazine, material contrast, subtle
   recoil. Its visual transform is kept apart from the hitscan's origin and from the authoritative aim.
5. The movement, the collision, the source hashes and the replay self-test preserved.
6. Screenshots and performance compared before and after, and no performance improvement claimed without measuring
   it.

His advice beside the list: depth comes from the environment (overhead beams, recesses, windows, distant structures,
controlled shadowing). Improve the WebGL 1 renderer first. Change the technology (WebGL 2; Three.js or Babylon.js;
Godot or Unreal) only if it is needed later.

**His rule: three worlds.** The canonical world says what the map means. The collision world says what blocks
movement and shots. The render world says how it looks. In his words: *"The renderer can add bolts, trim, decals,
surface detail, particles, lighting, and decorative meshes. It must not silently decide where walls, cover, or
player-blocking objects exist. If visual decoration is intended to affect gameplay, that change must be represented in
the authoritative world and checked."*

**Grade.** DECLARED: his ruling. It is not a rung, and it adds no row.

**Built (2026-10-09), beside the certified tree.** `python graybox/serve.py` now draws with a new
`graybox/web/render.js`, still WebGL 1. The first renderer is kept as `render_flat.js`, unchanged but for its name
(`--renderer flat`, or `?renderer=flat` in the address), so the two can be compared and the change undone.

| his item | what stands |
|---|---|
| 1. sky and light | a sky gradient with a sun disc and thin cloud, per pixel; one sun, 40° up, whose shadow is traced through the canonical world's heights (a texel a cell, each cell a column), with a soft outer edge; light from the sky above and from the ground below; darkening at the foot of walls and in inside corners, from the same heights; distance haze in the sky's colour; a filmic tone curve |
| 2. floors | a module a cell: poured concrete slabs, each sawn once across; steel tread plate at the bases, with the base's border and a spawn pad in the team's colour; a painted steel deck on the platform, welded every metre, striped where it drops; a painted border where the layout has stairs; the objective painted on the deck as a ring. The 1 m grid is an overlay: G, or `?grid=1` |
| 3. walls and cover | formed concrete panels with joints and tie holes, a dark baseboard, a steel cap; windows painted on about one panel in five; steel guards on outside corners; a thin team band near the bases. Low cover is dressed as a wooden crate, an olive container or a concrete barrier, tall cover as a concrete column or stacked containers, chosen once for each group of cells; the platform's risers striped. Each is the column's own box: no dressing is larger or smaller than what blocks |
| 4. the weapon | 22 parts: receiver, rail, handguard, barrel, gas block, muzzle device, front and rear sights, magazine well and a magazine raked forward, grip, trigger and guard, buffer tube, stock and pad, charging handle, ejection port. They are in gunmetal, black polymer, tan polymer and steel. A kick read from the weapon's cooldown, a sway from the look, a bob from the distance walked; a muzzle flash that lights the scene; a streak to where the shot ended. The weapon has its own projection and is drawn over the world. The shot stays the simulation's: from the eye along `Sim.aim`. The weapon's transform enters nothing |
| 5. preserved | `sim.js` byte for byte (sha256 `86c7e5fe…`); `level.py`, `check.py` and the maps untouched, so the canonical and collision hashes are the same; every earlier check of the runtime's self-test passes; `render.js` calls one function of the simulation, `Sim.aim`, and reads its constants |
| 6. compared | `serve.py --bench` draws the same poses (each spawn, the middle of each route, a shot) with both renderers at the same size, alternating, and writes a screenshot of each pose by each, with the timings, to `graybox/build/bench/MAP/` |

**Depth.** Beams rest on the wall tops across short runs of open cells, on every fourth row and column. A skyline of
44 blocks stands outside the map. Windows and recesses are painted, not cut: a recess cut into a wall would be the
render world deciding where the wall is.

**His rule, as the self-test holds it.** Three checks were added, beside `render-flat`, which builds and draws the
first renderer. `render-readonly`: the whole state, and its hash, are the same before and after six frames drawn by
both renderers mid-shot. `render-conforms`, against the collision world:

- every top the lit renderer draws is at its cell's height in C, one to a cell;
- every upright face runs from the lower neighbour's height to its cell's;
- every step of C has its face, and there is no other solid in the world mesh;
- each decoration block is outside the map, or above the play ceiling;
- the target is drawn inside its hit box.

The play ceiling is the highest eye a player can reach. The check finds it with its own search from the spawns, on
the movement's numbers (a rise of at most a jump's height and a step): 3.845 m on the tactical map, 2.845 m on the
witness level. The beams sit at 4 m and above, and a line between two points below the ceiling stays below it. So no
decoration stands between an eye and anything it can shoot.

Seven defects were planted in the renderer, each refused by its check:

- a cover top drawn 0.3 m above what blocks;
- a step's face left out;
- the beams lowered into play;
- a block of decoration on a route;
- the target drawn past its hit box;
- the renderer writing the state;
- the renderer turning the view.

A first form of the sixth wrote a value the state already held at that moment (the shot had hit, so the hit marker
was above it). It changed nothing, and was replaced by a write that does change something.

**What it does not do.** A shot aimed at a beam passes through it, and a player can see that. The targets' shadows
are soft blobs, not traced; nothing casts a shadow but the heightfield's columns. There are no textures and no normal
maps: every surface is computed in the shader. The anti-aliasing is what the browser gives.

**Run here.** In the build container, in headless Chromium (SwiftShader, a CPU rasterizer):

- the runtime's self-test, 23 / 23 on the tactical map and 20 / 20 on the witness level, through `serve.py
  --selftest`, which ended 0;
- the seven plants;
- the bench, ten samples a pose and renderer at 1280 × 720. The tactical map: the first renderer about 58 ms, the lit
  one about 1.15 s (the medians of all samples), about 17 to 21 times as long, pose by pose. The witness level: about
  77 ms and about 1.52 s, about 17 to 22 times.

On a CPU rasterizer that is the cost of the arithmetic per pixel. It says nothing of a GPU. Before and after are in
the screenshots.

**Grade.** OBSERVED (the build container): the self-test, the plants, the screenshots. MEASURED, in SwiftShader only:
the bench above. NOT_MEASURED: the lit renderer's cost on the owner's GPU, and so any frame rate; feel. No
performance improvement is claimed. It is not a rung of the gate, and adds no row.

**On the host (2026-10-09).** 0174 to 0177 applied on `3dc15ec`, after a direct check of the Git state:

- no `status.showUntrackedFiles` setting;
- an empty status with every untracked file shown;
- no file flagged assume-unchanged or skip-worktree;
- `HEAD` and its upstream both `3dc15ece…`.

The tree after was `c1a8b5f6…`. The tree given to the owner beforehand, `63bfc87b…`, was the build container's, and
it was wrong for his checkout. His history holds 40 host records he committed himself (`kernel/attest/` and
`shell/attest/`, each `-DANIELDILLBERG`), which the container never had. The same four patch files applied to the
pushed `3dc15ec`, cloned from GitHub, give `c1a8b5f6…` exactly. The two trees differ by those 40 added files and by
nothing else. The container now works on the pushed history.

On his machine:

- the map checks with `--compile`: every check and mutation passing on both maps, and the tactical layout compiled
  and admitted again to head `c862f3b1aee2`;
- the self-test, 23 / 23 on the tactical map, each line as in the container, down to the replay's last hash
  `91350c39A` and the read-only check's `9613beecA`;
- the bench, run twice, in Firefox 157 on Windows, through ANGLE on Direct3D 11 to an AMD GPU. It ran at 1280 × 720
  with 20 samples of one draw each. *(Corrected 2026-10-09, after the record was written: it said "a Radeon R9 200-series GPU". The browser
reported "ANGLE (AMD, Radeon R9 200 Series Direct3D11 vs_5_0 ps_5_0), or similar", the name Firefox gives a
whole family of AMD GPUs; the model is not established. [`RESEARCH-FINDINGS.md`](RESEARCH-FINDINGS.md), R-8.)*

The first renderer's medians were 1.0 to 1.5 ms a pose. The lit renderer's were 1.0 to 2.0 ms. Every timing was a
whole millisecond, and no sample passed 4 ms. The page's clock in that browser advanced a millisecond at a time, so
the difference between the two renderers is within the clock's step. The column headed p95 was in fact the maximum,
an error of rank in `serve.py` at 20 samples.

The witness level's self-test was not run there. Then he played, and **the mouse was not captured**.

**The cause.** Until the mouse is captured, an overlay covers the view and asks for a click. The click landed on the
overlay. Only the view listened for it, so the lock was never asked for. It had been so since 0175, and nothing here
met it: the container's runs hid the overlay by script, and a headless browser plays no one's click.

**The repair (0178).** A click on the overlay or the view asks for the lock. A refusal is shown on the overlay, and a
second click asks again. It is checked off the repository, in headless Chromium, with the browser's lock replaced by
a recorder, so that no emulated cursor enters. Seven checks pass:

- a click where the player clicks asks for the lock;
- the overlay goes;
- 100 px of movement turns the view by 0.22 rad;
- released, the overlay returns;
- released, movement turns nothing;
- a refusal is shown;
- a second click captures.

The 0177 page fails the first three. The bench's sample is now the mean of a batch of draws, each read back. The
page's clock step is printed, and p95 is the nearest rank. `serve.py` asks the browser to isolate the page from other
origins, which gives the page a finer clock in a browser that rounds it.

**Grade.** OBSERVED (the host): the Git state, the tree, the map checks, the self-test, the capture failure. MEASURED
(the host, a 1 ms clock): both renderers about one to two milliseconds a draw and readback at the median, at 1280 ×
720. Their difference is not resolved by that clock. OBSERVED (the build container): the repair's seven checks. NOT
MEASURED: a frame rate; the capture on the host after the repair; feel. Not pushed yet.

**After the repair, on the host (2026-10-09).** 0178 and 0179 applied. The tree was `1275b4f4…`, as predicted
beforehand from the pushed history (lesson 74, met). On his machine:

- the self-test, 23 / 23 on the tactical map and, for the first time there, 20 / 20 on the witness level, each line as
  in the container;
- the bench, with the page now isolated, so its clock stepped by 0.02 ms. Each sample was the mean of ten draws, each
  read back; 20 samples a pose, at 1280 × 720, in Firefox 157 on the same AMD GPU (its model not established; see the correction above).

| pose | first renderer p50 / p95 ms | lit renderer p50 / p95 ms |
|---|---|---|
| spawn A | 1.172 / 1.310 | 1.753 / 2.036 |
| spawn B | 1.177 / 1.354 | 1.670 / 1.780 |
| route mid | 1.229 / 1.654 | 1.666 / 2.240 |
| route north | 1.179 / 1.294 | 1.677 / 1.834 |
| route south | 1.210 / 1.270 | 1.855 / 2.026 |
| firing | 1.220 / 1.376 | 1.821 / 1.998 |

The lit renderer took 1.36 to 1.53 times the first renderer's median: 0.44 to 0.65 ms more for each draw and
readback. No sample of either passed 2.34 ms. The 17- to 22-fold seen in SwiftShader said nothing of this GPU, as the
build had said it would not.

Then he played, and reported: *the play felt really crisp for a first play.* The capture is taken as working from
that report; no instrument saw it. Pushed, `3dc15ec..222f856`.

**Grade.** MEASURED (the host, one run, a 0.02 ms clock): the table, a draw and its readback, which is not a frame
rate and not input-to-photon. OBSERVED (the host): the tree, the two self-tests. DECLARED: his report of the play.
NOT_MEASURED: a frame rate; input-to-photon; any other browser or machine.

### NATIVE-PLAZA-0 — the plaza played without Unreal · **the owner's rulings** (2026-10-10, 2026-10-11); outside the certified gate · **built** (`art/play.py`, `art/web/`); its two rounds evaluated, not yet chosen; live edits built

**His rulings.** On 2026-10-10: *"Make Verðandi-native the primary architecture. Keep UE5.8 as a secondary
interoperability path. Do not make Unreal a prerequisite for authoring, compilation, or the eventual playable
product."* His success criterion: *"the same canonical art and layout sources can produce a playable native scene
without launching Unreal Editor."*

On 2026-10-11, answering the session's two questions: *"Choose the art-owned launcher (`art/play.py`) and WebGL2 in the
browser. Keep `serve.py` and the existing `graybox/` boundary unchanged."* He asked that the scene be served *"as a
generated artifact"*, with the name validated and *"the launcher's allowed reads explicit"*, and set a narrow first
slice:

1. compile the admitted scene;
2. launch it through `art/play.py` with WebGL 2;
3. preserve movement and collision;
4. *"Demonstrate one natural-language visual edit, such as making the cantilevers more imposing, without
   unintentionally changing the playable layout"*;
5. compare the registered views and inspect the result in motion.

**Built (2026-10-11).**

- **`art/play.py`.** It compiles the brief, holds the scene to the art checks (a scene that fails one is not served),
  and serves six named paths on 127.0.0.1. It writes nothing. `graybox/serve.py` is unchanged.
- **The page.** The graybox's `sim.js`, served unchanged, moves the player against C. Keys 1–9 move a camera to the
  brief's views, not the player.
- **`art/web/scene_render.js`, WebGL 2.**
  - The moon's shadow.
  - Every lamp, neon and downlight, each seen only from the cells it can see across the grid, so no light leaks
    through a wall.
  - Surfaces patterned by what they are: board-formed concrete with tie holes and drips, stone setts, black water,
    steel.
  - Light thrown up from the lit floor onto undersides, and the sky dimmed by the masses around and above.
  - Height fog and each lamp's glow in it, the wet floor and the puddles as mirrors, rain and its rings, bloom.
- **The exporter's new options**, recorded in the ledger by a rebase (#14): `tower … mass` (stepped masses with
  cornices) and the canopy's `deep`, `ribs` and `lit`. No statement of the brief used them, so the scene's bytes were
  unchanged. A new plant in `art/check.py` was meant to refuse ribs that hang below the reach ceiling under a slab that
  clears it; its slab did not clear it, so it showed nothing about the ribs (found and fixed below).
- **The director's self-test** now holds its fixture to the art and the world the round was written against, not
  to the exporter, which is the program under test.

**The edit, through the loop.** Two rounds, written by the model at head `cac46b5c8e28` and evaluated:

- **"make the towers read as one monumental mass, not a comb"** (`art/rounds/plaza-mass/`, #15 to #17): A, B and C,
  all CLEAN.
- **"make the cantilevers more imposing"** (`art/rounds/plaza-cantilevers/`, #18 to #20): A, B and C, all CLEAN.
  Every candidate changes the canopies and nothing else; the play boxes are the same 87.

Nothing is admitted until he chooses.

**Judged from the native renderer's stills** (OBSERVED, in a software renderer in the build container):

- Massing: from above, the head reads as a comb. A, B and C read as stepped blocks with cornices, and C's crown is the
  strongest.
- Cantilevers: A's ribs are lost in the dark. B's downlights make the soffits read. C, the ribs and the light
  together, reads as a structure.
- The washed wall of the north flank, a lamp over every cell, shows as the earlier note said.

Walk-throughs of the recorded walk, as frame sequences, were made for the head and for mass A with cantilevers C.

**What it does not show.** That the picture is good: a person judges it. That it runs at any frame rate on any
machine: nothing was timed. That the look is AAA: it is the first native renderer, boxes with procedural surfaces, no
global illumination, no textures, and no shadows from the point lights.

**The host run (2026-10-11).** 0189 and 0190 applied as tree `aa7ddc63…`, as predicted; the ledger verified at 21
events, the director's self-test and the art checks passed, the graybox self-test 27 / 27, and `art\play.py
plaza-night` launched on his machine. Pushed `3eeab82..1b5e8f6`.

**Live edits (2026-10-11), at his request.** He asked to *"load the edit into the live world without closing the
program"* when a model writes a change. Read first: Ursprung's `weltwerk` (commit `dcdad67`). Its rule, in
`sim/world_edit.py`, is that an edit is *"NEW authority, not mutate existing truth"*: a rejected edit leaves the old
world standing, and the player's own state is carried through untouched. Its `apply_edit` gates an edit with the
authoring layer's parse, pre-play validation and consequence diff; the tests pass here (the seven authoring suites,
and `sim/test_world_edit.py` 9 / 9). Its prototype page (`fps_demo/weltwerk_fps_prototype.html`, F8) has a live
editor: text typed into the page rebuilds the world in place, the player's state kept. That editor is a JavaScript
mirror of `apply_edit` that refuses only empty text, not the Python gate, and nothing reaches it from a file a model
writes. Verðandi takes the rule, not the code: the checks stay with the authority (the art checks and the director),
and the file a model writes is what the running page shows, or refuses.

- **`art/play.py`.** Sources: the brief (or `--art`), and each `--intent FILE`, the brief with the intent applied as
  `director.py` evaluates it (a REFUSED candidate is not served; nothing is written to the ledger). A thread watches
  the files each source is made from; when their bytes change, the sources that depend on them are compiled again in
  a fresh Python process, so that an edit to the exporter is used too, and held to the same checks. What passes is
  served; what does not leaves the scene before it served, with the reason. `/live` says what is served.
- **The page.** It asks `/live` twice a second. A new scene on the same map is fetched, held to its digest and drawn
  in place (`Renderer.load`, the old scene's GL objects freed). The game is not touched: the renderer writes no
  state. A new map is a new collision world and so a new game at the spawn, nothing of the old one carried into it.
  A new renderer file takes the canvas over, or, if it does not start, the old one goes on drawing. A new `play.js`
  or `sim.js` is announced, for a reload. `[` and `]` step through the sources.
- **`python art/play.py --selftest`**, without a browser, 13 / 13: the paths served and no others; an edit served, and
  equal to compiling that text in place; a touch that changes no byte compiles nothing; an edit to the intent compiles
  that source alone; five refusals (a canopy where a player can be, a statement the exporter cannot read, an intent
  naming no statement, an intent whose candidate fails a check, the compiler stopping), each leaving the scene before
  it served. Seven mutants of `play.py`, each refused by at least one check.
- **In a browser, in the build container** (Chromium with a software renderer; the harness is not committed), 11 / 11:
  an intent rewritten from C to A was drawn 0.9 s after the write, with no reload, the state object, the world and the
  snapshot the same, and the game went on (tick 62 to 95); a refusal was shown and the scene kept; an art edit
  drawn; the renderer's file swapped, and a planted one that does not start refused; a change to `play.js`
  announced; a layout candidate (the south flank closed to a slot, CLEAN) started a new game at the spawn; no page
  errors. OBSERVED, these runs.
- **What it does not show.** A frame rate, or the swap's cost on a GPU: nothing was timed on the host. That the GPU's
  memory is returned: `dispose` deletes every object the renderer made, which was not measured. An editor that
  writes a file in pieces is met by waiting for the file to hold still and, if a piece is read, by a refusal; not by
  an atomic write.

**A plant that proved nothing, found and fixed.** 0190's plant *"a canopy clear of every head whose ribs are not"*
set its slab at 3.6 m, below the reach ceiling over the platform's middle (4.275 m), so the slab itself was refused
and the plant said nothing about the ribs. Each canopy option's plant now shows the slab alone passing and the slab
with the option refused: the ribs under a slab at 4.4 m, and a new plant for the edge lights.

**The owner's art note on the cantilevers (2026-10-11).** *"Make the nearest cantilever lower and larger in frame, then
keep its underside mostly dark with a narrow row of warm fixtures along the edge."* And: *"The comparison labels and
borders also occupy enough space to interrupt the architectural read."*

- **The exporter.** The canopy's `edgelit R,G,B CANDELAS`: a narrow row of small fixtures, one a metre, along the edge
  that faces the region's middle, each with its light. Recorded by a rebase (#21, head `cac46b5c8e28` to
  `1ff8e5e8f6be`); the brief uses it nowhere, so its scene's bytes are unchanged.
- **D** (#22, CLEAN): the north slab alone, from 7.0 m down to 4.6 m and 2.2 m deep, over the same two rows, dark
  beneath but for the warm row along its plaza edge. A version over a third row was rendered and set aside: the
  plaza's pole lamps would stand under it, 0.1 m below the slab, and light its underside.
- **E** (#23, CLEAN): D's north slab with the far slabs as in C.
- The ledger verifies at 24 events, head `d22e7cb24356`. The play boxes are the same 87.
- **The sheet.** The stills, from the round's views, are set edge to edge with a 2-pixel gap and a small label inside
  the first row, nothing between the pictures. Judged from them (OBSERVED, software renderer): D's slab is lower and
  larger in frame, a dark mass with a warm line along its edge, the magenta neon still below it. Nothing is admitted
  until he chooses.

**The host run of 0191–0193 (2026-10-11).** Applied as tree `a8d7b03a…`, as predicted. The art checks passed (with
both canopy-option plants showing the slab alone passing), the ledger verified at 24 events (head `d22e7cb24356`, the
files at `1ff8e5e8f6be`), `art\play.py --selftest` 13 / 13, the certified gate passed (251 rows / 0 fail, rowset
`74db4c8d78625af5`), and `art\play.py plaza-night` with C, D and E as sources launched, watching 19 files. Pushed
`1b5e8f6..30d2527`. OBSERVED once.

### DET-MATH-0 — the simulation's rules made portable · **the owner's ruling** (2026-10-11); outside the certified gate · **built** (`graybox/web/sim.js` rules 1, `graybox/rules_ref.py`, `graybox/trace.py`)

**His ruling.** *"My revised ruling: investigate and implement the deterministic math layer now."* *"I would not wait
for the desktop renderer or networking. The browser runtime is already a useful place to establish the simulation
contract."* In four steps: identify every transcendental operation that can affect authoritative state, *"including
the bot's input generation"*; specify deterministic replacements, *"fixed-point/integer formulations where practical,
or carefully specified software implementations with explicit range reduction and rounding"*, since *"Simply
replacing `hypot` with `sqrt(a*a+b*b)` is not sufficient"*; *"run the same input sequence through Firefox and
Chromium, comparing per-tick authoritative state and identifying the first differing field"*, the replay hashes kept
*"as a compatibility measurement, not the sole correctness criterion"*; and decide what must be bit-identical. *"If
you change the math now, replay hashes may change. That is acceptable if you deliberately version the simulation
behavior and preserve the old baseline for comparison."* And the scope: *"Keep the scope limited to authoritative
state, and let the measured divergence—not a blanket desire for identical math—determine which operations need
replacement."*

**1. The census.** Every call of a function whose last bits ECMA-262 leaves to the engine, in `sim.js`: `Math.sin` and
`Math.cos` of the yaw in `step` (the walking direction) and of the yaw and pitch in `aim` (the shot: a hit or a
miss); `Math.hypot` in `step` (the step's length); `Math.hypot` and `Math.atan2` in the bot (`walk`: when a waypoint is
reached, and the turn it inputs), in `lines` and `makeRuns` (the fight's start cell, yaw and pitch), and in the
self-test's own walkers and shooters. Nothing else a tick does is the engine's choice; no numeric literal in `sim.js`
has more than 20 significant digits (ECMA-262 lets an engine round a longer one either way); and `hash` read the
platform's byte order through a `Float64Array`, now written with a DataView, little-endian, which every platform a
browser runs on already is (its values unchanged). Outside the authoritative state, and left as they are: the
renderers, the mini-map and the page's measurements in `main.js`. The art's build (`art/dress.py`) uses no such
function (one exact integer power), so its outputs do not depend on the platform's libm. The measured divergence: node
22 against Chromium 141, `sin` and `cos`; the owner's Firefox 157 against Chromium 141, `hypot` on about a quarter
and `sin` on one (R-6). `atan2` was not seen to differ in either pair; it is replaced too, since it makes the bot's
inputs and the fight's start and the specification leaves it to the engine. That goes one function beyond the
measured divergence, and is his to reverse.

**2. The replacements**, in `sim.js`, built only from `+ - * / %`, comparisons, `Math.floor`, `ceil`, `min`, `max`,
`abs`, `imul`, the bit operators, DataView's access to a double's bits and BigInt:

- `xsin`, `xcos`: fdlibm 5.3's algorithm: a Cody–Waite reduction by pi/2 in three 33-bit parts, a second and third
  step when the first cancels, the kernels' polynomials. Defined for |x| ≤ 2²⁰ · pi/2; beyond it, a `RangeError`.
- `xatan2`: fdlibm 5.3's, with FreeBSD's correction for |y/x| > 2⁶⁰.
- `xsqrt`, correctly rounded, by an integer square root in BigInt, not `Math.sqrt` (whose exactness the sources this
  session found disagree on).
- `xhypot`, correctly rounded: the squares summed exactly in BigInt, so no step overflows or underflows, subnormals
  rounded as subnormals, `Infinity` only when the rounded result is.
- Every constant written as its double's bits.

A fixed-point tick (integer positions and angles) would be the stronger form; it changes every number in the state
and every reader of it, the renderers included. These replacements keep the state's form and change only the
functions, so rules 1 differ from rules 0 at exactly the calls the census names.

**3. The same inputs in two engines.** `trace.py` now plays the three runs (the walk, the fight, and a new stress run of
3,600 ticks made from integers alone) under rules 0 and rules 1 in one trace, and `--inputs A.json` plays A's runs,
so that two browsers play exactly the same sequence; `compare` gives, rules by rules, each function's differing
results, the first differing call, and each run's first differing tick with its fields. In the build container, node
(V8 12.4) against Chromium 141 (V8 14.1) on the same inputs: under rules 0, `sin` and `cos` differ on 112 and 99
arguments and every state is still the same; under rules 1, no call of the engine's Math and every state of every run
the same at every tick. Within Chromium, rules 0 and rules 1 part on the stress run at tick 490, in `x`, by one ulp.
**Firefox against Chromium on his machine is the measurement this step asks for, and it is his to run** (the
commands are with the patch). Until then, rules 1's identity in SpiderMonkey rests on the specification: NOT
MEASURED.

**4. What must be bit-identical** (rules 1; `graybox/README.md`, *The simulation's contract*): the world built from
the map's bytes; the transition, as the next state's snapshot bytes; the serialized state (snapshot, restore, hash);
the inputs a run is made of (the bot's walk, the fight's start, the stress run); and the rules' arithmetic. Not: the
renderers, the view's feedback, the HUD, timings, the measurements. A player's own input is data, recorded as bits.

**Versioning.** `Sim.RULES` is 1; `Sim.withRules(0)` builds the rules as they were, for the measurements and the trace
only. The self-test prints rules 0's replay against its baseline (`91350c39A` tactical, `ce819a52A` witness, recorded
2026-10-10) as a measurement. Rules 1's replay of the walk ends at the same hashes on both maps in these runs: the
engine's last bits were absorbed there, as before.

**Held by.** Two self-test checks, each with plants: `rules-arithmetic` (the 43 constants; each function's results
over 4,000 arguments against `rules_ref.py`'s digest; 31 special values; the sine's domain) and `math-fence` (Math's
23 approximated functions made to throw while the runs are recorded and played: the same states; the source naming
none of them). Eleven mutants of `sim.js`, each refused. `graybox/rules_ref.py`: the same algorithms in Python, the
digests and constants agreed, the square root and hypot checked exactly against their neighbours' midpoints, and the
accuracy measured against 70 decimal digits (sine 0.70 ulp, cosine 0.74, atan2 1.06 on the first 1,000 of each set;
a sweep of 20,000 found atan2 at 1.23, fdlibm's own). The self-test is now 29 / 29 on the tactical map and 26 / 26 on
the witness level (Chromium, 10.5 s and 8.6 s in the container's software renderer).

**Measured cost.** About 4.2–4.6 µs a tick under rules 1, 1.4 µs under rules 0 (node, the container): BigInt's exact
hypot, once a moving tick. A development measurement, not a row.

**What it does not show.** That SpiderMonkey or JavaScriptCore give the same bits (until a trace from them is
compared). That an engine has no defect in the operations rules 1 rely on. That the movement's own numbers are
robust: rules 1 make the same bits everywhere, not better physics. Nothing here enters the certified gate.

**On the owner's machine (2026-10-11).** 0194 and 0195 applied as tree `12a540fc…`, as predicted; `rules_ref.py`
passed; the self-test in Firefox 157, 29 / 29 and 26 / 26, `rules-arithmetic` and `math-fence` among them (so
SpiderMonkey's results for the five functions on all 20,000 arguments are CPython's); its own `Math` against the
rules': `sin` different on 70, `cos` on 62, `hypot` on 693, `atan2` and `sqrt` on none, of 4,000 each; rules 0's
baselines reproduced; the gate 251 rows / 0 fail; pushed `30d2527..0430b6c`. His Firefox trace's digests of every
tick's state under rules 1 (the walk `207902cee453d357`, the fight `33e990dd20b743f8`, the stress `5b068df47e0b2e1a`)
are the build container's Chromium 141's and node 22's, on the same inputs (`38f78768…`, `ee469f56…`, `7374b8c6…`);
under rules 0 the stress run's differ (`99015929…` in Firefox, `6faecae7…` in V8). OBSERVED once, across two
machines, at the level of a digest over every snapshot.

**His ruling.** *"ACCEPT DET-MATH-0 as the right architectural direction, with one remaining measurement gap: Firefox
has not yet been compared against an independently identified Chromium run on the same recorded inputs."* The run
meant as Chromium's identified itself as Firefox 157: *"That comparison is Firefox against a second playback of the
Firefox trace—not Firefox against Chromium."* So: versioned deterministic math ACCEPT; the Python arithmetic reference
ACCEPT, within its coverage; rules 1's cross-browser equivalence NOT ESTABLISHED until the two-browser comparison; the
full Python tick NEXT; a Rust port deferred until the tick and its contract are stable. *"Continue the art loop in
parallel."*

**The correction, in `trace.py`.** The `--no-browser` address had been opened in the default browser, and `--name
chromium` wrote what came back under that name. Now `--browser msedge` (or `chrome`, `firefox`) opens the page in
the browser named and expects a trace from its engine family; `--expect FAMILY` says the same without opening one; a
trace from another family is refused and not written; and a trace is written under the engine it reports and its
family (`chromium-given.json` is a Chromium engine's), a `--name` that names a family only if it is the trace's.
`compare` now says what kind of comparison it is: `NOT A CROSS-ENGINE COMPARISON` when both traces describe the same
browser, two builds of one family, or cross-engine. Its self-test holds the engine families of five browsers'
descriptions and both verdicts.

**The two browsers on one machine (2026-10-11).** 0196 and 0197 applied as trees `b0b5f0ff…` and `e5f313ef…`, as
predicted. With `trace.py run tactical --inputs graybox/build/trace/tactical/firefox.json`, Edge 155 (`--browser
msedge`; it described itself as `Chrome/155` and `Edg/155`, a Chromium engine, and the trace was accepted as one) and
Firefox 157 (`--browser firefox`) played the runs his Firefox had recorded (given-runs digest `c97d5035…`), and
`compare` called the pair cross-engine, Firefox against Chromium. Under rules 1: no call of the engine's `Math` in
either, and every snapshot the same bytes at every tick of the walk (1,787 ticks), the fight (476) and the stress run
(3,600). Under rules 0, the same machine and the same inputs: `Math.sin` different on 103 of 4,307 common arguments,
`Math.cos` on 98 of 4,307, `Math.hypot` on 1,414 of 4,084, each difference shown one ulp; the first differing call the
1,424th, at the walk's tick 475, in a result (`hypot(0.14834045293008993, -0.9889363528683207)`: 1.0 in Firefox,
0.9999999999999999 in Edge); the walk's and the fight's states still the same at every tick, and the stress run's
parted at tick 490, in `x`, by one ulp. The gate 251 rows / 0 fail; pushed `0430b6c..514a45e`.

So the comparison his ruling named has been made once: on one machine, on one map's three runs, field by field,
rules 1's states are the same in SpiderMonkey and in V8, and rules 0's are not. MEASURED once. Not the witness level,
not another machine's Firefox, not JavaScriptCore, not other builds. Whether it moves rules 1's cross-browser
equivalence from NOT ESTABLISHED is his to rule. Three things the same run shows besides, each OBSERVED in these runs
only:

- Rules 1's digests of every tick's state on these inputs (the walk `207902ce…`, the fight `33e990dd…`, the stress
  `5b068df4…`) are those Chromium 141 and node 22 gave in the build container: three V8s on two machines,
  SpiderMonkey, and (through `tick_ref.py`, below) CPython.
- The runs his Firefox recorded itself under rules 1 are, byte for byte, the runs Chromium 141 recorded in the
  container (the same given-runs digest, `c97d5035…`): the bot's walk, which calls atan2 and hypot at every tick, and
  the fight's start came out the same in both engines.
- Under rules 0, the stress run's digest is the same in every V8 measured (node 22 and Chromium 141 in the container,
  Edge 155 on his machine: `6faecae7…`) and in both Firefox runs (`99015929…`): in these runs, rules 0's states were
  a property of the engine family, not of the machine.

**His ruling (2026-10-11, after that run).** *"DET-MATH-0 advances from NOT ESTABLISHED to MEASURED once for
cross-browser equivalence on the tactical map."* *"This is not a universal cross-engine proof, but it satisfies the
specific comparison previously missing."* *"The rules-0 stress divergence is a useful control showing that the
experiment can expose a real difference."* And one result he asked to keep: *"input equality, initial-state equality,
per-tick state equality, and individual arithmetic tests catch different defects. None subsumes the others."*

### TICK-REF-0 — the tick a second time, in Python · **the owner's ruling** (2026-10-11): "Full Python simulation tick — NEXT"; outside the certified gate · **built** (`graybox/RULES-1.md`, `graybox/tick_ref.py`)

**His ruling.** *"Browser JavaScript records the input sequence. Python independently advances the authoritative
simulation. Each tick's expected snapshot is compared with the browser's snapshot. The first mismatch identifies the
tick and state field. The reference implementation does not call into the browser simulation or trust its computed
result."* *"Keep the Python implementation independent in structure, not merely a line-for-line translation. Share
the specified rules and test vectors, but avoid sharing implementation helpers that could reproduce the same defect
in both implementations."* And its limit: *"It is not yet proof of server security, network protocol correctness, or
resistance to malicious inputs."*

**Built.**

- **`graybox/RULES-1.md`**, the specification: the arithmetic (each operation rounded, evaluated left to right; what
  `floor`, `fmod`, `max` and `min` mean at −0 and NaN, and where Python's own differ), the constants, the world, the
  state, one tick in nine steps, firing, the wall's distance, a box's entry distance, the snapshot and the inputs.
  Independence in structure is possible; independence in arithmetic is not: two programs reach the same bits only
  by the same roundings, so every formula is fixed operation by operation.
- **`graybox/tick_ref.py`**, written from it: its own state (classes, not a walked object), world, collision walk,
  ray walk, snapshot writer and reader, and square root and hypot (Python's integer square root, not the BigInt
  Newton iteration of `sim.js`). The sine, cosine and atan2 are fdlibm's, from `rules_ref.py`, which is itself a
  separate implementation held to every result. `verify TRACE.json` converts the map the trace names and holds it to
  the trace's manifest, makes the stress run's inputs and start again from integers, and plays every rules-1 run from
  its start with the browser's inputs, comparing every snapshot byte for byte and naming the first differing tick and
  its fields. It trusts nothing the browser computed but the inputs and the bot's runs' starts, read back exactly.
- **Its self-test**, on any trace: two plants in the trace (a field one bit off at tick 1,000, found there in `x`;
  an input of the walk changed at tick 300, found there) and six in the Python tick (the height's two updates in
  the wrong order, five halvings for six, the shot's direction with the wrong sign, a target standing again at 0,
  the sine's polynomial cut short, the cells scanned from the centre), each found; and the specification's numbers
  are `sim.js`'s.

**Measured in the build container (2026-10-11).** Chromium 141's and node 22's traces, the tactical map (5,863 ticks)
and the witness level (5,247): every snapshot the same bytes as the browser's, and the stress runs' inputs and starts
made again in Python the same. 0.65 s for a trace. One finding about the method: a defect of one place in the last bit
can be absorbed by a run. The plain root of the sum for hypot parts from the browser on the tactical walk at tick
1,172 and never on the witness level's runs, and a sine reduced without its tail is absorbed there too. A tick-level
comparison does not replace the arithmetic's own check, result by result (`rules_ref.py`); the two hold different
things.

**What it does not show.** The owner's limits: not a server's security, a protocol, or resistance to malicious inputs.
Nor that the bot's input generation is the same in Python (it is not implemented here; the stress run's inputs are).
Firefox's and Chromium's traces on his machine are the next measurement for it, as for DET-MATH-0.

**On the owner's machine (2026-10-11).** `tick_ref.py verify` on his Firefox 157's own trace: the map converted there
with the trace's digests (canonical `9e179490cafe`, collision `467b52595504`), every snapshot of the walk (1,787 ticks),
the fight (476) and the stress run (3,600) the same bytes as Firefox's, and the stress run's inputs and start made
again the same: `TICK REFERENCE VERIFIED`, 5,863 ticks. Its self-test on Firefox's given-runs trace passed: the trace
verifies, the constants are `sim.js`'s, both plants in the trace found at their ticks (1,000, in `x`; 300), and the six
plants in the reference each found exactly where the container's self-test finds them (the fight at tick 23, the
stress run at 679, the fight at 1, the fight at 300, the walk at 475, the walk at 961). So the Python tick gives the
same bytes as SpiderMonkey, as well as V8, on the tactical map's three runs: MEASURED once. Edge's own trace was not
given to `verify` (the command was in the list and not run). Its snapshots are Firefox's byte for byte (`compare`,
above), so they are the Python tick's too by that comparison; the direct run is among the next commands.

**His ruling.** *"I'd accept 0196/0197 provisionally from the reported results, then build this as the next vertical
slice"*: the Python bot that records the walk (BOT-REF-0).

**The direct run (2026-10-11).** `tick_ref.py verify` on Edge 155's own trace of the given runs: every snapshot of the
walk, the fight and the stress run the same bytes as Edge's, and the stress run's inputs and start made again the
same: `TICK REFERENCE VERIFIED`, 5,863 ticks. Then on his machine, after BOT-REF-0, `tick_ref.py verify` on Firefox
157's and Edge 155's plays of the Python walk: each 1,787 ticks, VERIFIED. His ruling, made before the direct run was
reported: *"TICK-REF-0 — ACCEPT provisionally"*, *"Edge's trace still has not been directly passed through
`tick_ref.py verify`; the matching Firefox snapshots support the inference, but I would keep that direct check
outstanding."* It is no longer outstanding: run, and VERIFIED.

### BOT-REF-0 — the walk made in Python from the map alone · **the owner's ruling** (2026-10-11): "the next vertical slice"; outside the certified gate · **built** (`graybox/WALK-1.md`, `graybox/bot_ref.py`)

**His ruling.** *"Next piece: the Python bot that records the walk"*: *"It closes the gap between replaying a
browser-produced trace and independently generating a reference run from the map."* The bot *"should produce inputs
without consulting `sim.js`, browser state, or an existing browser trace."* Its contract, in six parts: independent
input generation (*"Do not port the JavaScript bot line-for-line if that merely duplicates hidden assumptions"*); a
deterministic policy; *"Separate policy from simulation. The bot chooses inputs; `tick_ref.py` alone advances
authoritative state. The bot must not read the resulting future state or use the browser's decisions"*; a canonical
trace, with *"map identity, initial-state bytes, rules version, bot-policy version, tick count, and the exact input
bytes per tick. Reject malformed or mismatched metadata"*; field-by-field verification against the existing browser
traces; and adversarial tests: *"Plant a defect in bot input generation, alter one input byte, change the map
identity, and perturb a tick result."* Two properties are kept apart: *"Reference reproducibility"* and
*"Cross-engine agreement"*. *"The first does not establish the second. And because the bot policy itself can be
wrong, matching Python output alone does not prove that the walk represents the intended behavior. Keep the existing
recorded browser traces as independent comparison evidence."* The individual math tests stay. *"Keep the scope
narrow: one tactical-map walk first"*, the witness level *"only after the tactical walk passes"*, and the gate not
expanded. The milestone: *"a browser is no longer needed to originate the reference walk, while browser runs remain
independent evidence that the reference model agrees with the actual engine."*

**Built.**

- **`graybox/WALK-1.md`**, the policy written down from what `sim.js`'s bot did, with the choices it had left unsaid:
  the route taken by name order (UTF-16 code units, as JavaScript sorts); the targets' cells closed to the plan,
  standing or not; the plan's climb read from cell top to cell top, not the rules' collision; the turn taken whole
  and the short way, forward only; a cell reached within 0.3 m, at the cost of a decision and no tick; progress
  measured before the tick, and the stall rule. The policy is versioned (`walk-1`) apart from the rules (`1`).
- **`graybox/bot_ref.py`**, written from it. The plan is a breadth-first search a layer at a time (`sim.js` keeps
  one queue). A decision is a pure function of the path, the bot's own memory and an observation, `(x, z, yaw)`,
  which the driver makes from the present state before each tick. The function is given nothing else, so it cannot
  read a later state. The tick is `tick_ref.py`'s. The bot's atan2 and hypot are the rules', from `rules_ref.py`.
  `make` writes the walk (`VERDANDI-BOT-TRACE 1`); `check` reads it and holds it; `compare` sets it beside a
  browser's trace; `selftest` plants defects. The reader refuses the whole file, with a code for each fault:
  `BOT-REF-BYTES`, `-KEYS`, `-FORMAT`, `-DIGEST`, `-RULES`, `-POLICY`, `-MAP`, `-ROUTE`, `-RUN`, `-TICKS`, `-INPUT`,
  `-START`.
- **`trace.py run --inputs BOT.json`**: a browser plays the walk, read as `bot_ref.py` reads it and refused whole
  otherwise. The trace records the runs as given by `bot-ref-walk-1` with the walk's digest, and `bot_ref.py compare`
  says when a browser played this walk's inputs rather than its own bot's.

**Measured in the build container (2026-10-11), the tactical map.**

- *Reference reproducibility.* The walk was made three times, here and in two fresh processes under `PYTHONHASHSEED`
  0 and 4242: the same bytes each time (the file's sha256 `0ff71da1…`, its digest `a75baf13…`), in 0.17 s. MEASURED.
- *The policy written down is the browsers' bot's.* The route `mid` (a path of 47 cells), 1,787 ticks: the start and
  every input the same bytes as the walk Chromium 141's own bot recorded. By the digest of all the inputs
  (`38f78768…`), it is also the walk his Firefox 157 recorded (field by field, his run next). MEASURED for Chromium,
  OBSERVED at a digest for Firefox.
- *Cross-engine agreement on inputs Python originated.* Chromium 141 (`--expect chromium`, its trace accepted as
  Chromium's) and node 22 (a harness in the container, not committed) played the walk. Every snapshot was the same
  bytes as the Python tick's, all 1,787 ticks, and `tick_ref.py verify` passed both. MEASURED, these two V8s.
- *The self-test* (`BOT-REF SELFTEST PASSED`). Its rows: the file's form read apart from the writer; the three
  makes; the walk read and held; the walk against the trace. The plants, each found: six defects in the policy
  (0.35 m for 0.3; the neighbours z before x; the turn not the short way; the routes in reverse order; a climb of
  1.0 m planned; the start facing north); one byte of an input changed (`BOT-REF-DIGEST`; resealed, made again
  otherwise at tick 300, and the browser's walk differs there); the map's digest and the map's name changed
  (`BOT-REF-MAP`); ten faults of form, each refused with its code; the Python tick's `x` one bit off at tick 1,000
  (named there, in `x`); walks that break what a walk is held to (a turn of 3.5 rad, a shot, the last 5 ticks cut,
  the `north` route's walk named `mid`, a path planned through walls and over any height); and a start wrong only in
  a field the first tick writes over.
- *Mutants of `bot_ref.py`'s own checks*: 23, of which 18 were refused by the self-test. The five that survived are
  each equivalent on this map. On the tactical map no open cell beside a wall is higher than 1.0 m, so the climb check
  refuses any path into a wall before the wall check can. No distance is exactly 0.3. The route names are ASCII,
  where JavaScript's order and Python's agree. Spawn A stands on the route's first waypoint, so leaving the start's
  feet as spawn A's changes nothing. The stall rule never fires, because each cell is reached within 40 ticks. Three
  of the eighteen were caught only after plants were added for them (the walk's end and its waypoints held apart;
  the start against the browser's); one, the file's keys unsorted, needed the form read apart from the writer.

**Findings.**

- **Four plants in the policy leave this walk byte for byte the same**: ±x searched in the other order, the targets'
  cells left open, a stall after 18 ticks, and the distance by the plain root of the sum (`sqrt(dx·dx + dz·dz)`).
  This walk is no evidence for those choices either way. The self-test reports them, with a fifth that depends on
  the machine (the platform's atan2, below), and does not require them. Another map, or the witness level, may
  exercise them.
- **The bot's arithmetic.** The plain root of the sum for the bot's distance is absorbed by this walk. CPython's own
  `math.atan2` (this machine's C library) parts from the rules' at tick 519, by 8.9 × 10⁻¹⁶ rad. A defect in the
  arithmetic can be absorbed by one run and shown by another, which is why the rules' arithmetic is held result by
  result, as his ruling keeps it.
- **Each comparison holds something the others cannot.** An input changed in its last bit (tick 300, `dyaw` 0 to
  5 × 10⁻³²⁴) leaves every state the same: the inputs show it, the states cannot. A start wrong only in a field the
  first tick writes over (`onObjective`) leaves every state the same: only the start's bytes show it. A Python tick's
  `x` one bit off at tick 1,000 is named at that tick; a walk made with that tick parts from the browser's inputs only
  at tick 1,016, because the bot's decisions carry a state's error into the inputs after a delay.

**His acceptance table, where it stands.**

| Claim | Required evidence | Where it stands |
|---|---|---|
| Python bot is deterministic | repeated clean runs produce byte-identical input traces | MEASURED in the container (three makes, two hash seeds); on his machine, two makes compared: next |
| Python reference tick is correct for those traces | every saved state matches, tick by tick and field by field | MEASURED: Chromium 141 and node 22 playing the Python walk, every snapshot the Python tick's |
| Browser engines agree with Python | same map, initial state and inputs; engine identity verified; every snapshot compared | Chromium 141 (identity checked by `--expect`) and node 22, MEASURED; Firefox and Edge on his machine, NOT MEASURED until his run |
| Bot matches intended gameplay behavior | explicit policy invariants and adversarial cases | the inputs, the path and the walk held, each with plants refused; six policy defects found; four choices not exercised by this walk. Not the walk a player would make |

**What it does not show.** That `walk-1` is the walk a player would make: the checks hold a walk to what a walk of a
route is for, nothing more. That Firefox and Edge agree with the Python walk: his run. The witness level, by his order
after the tactical walk passes. A server, a protocol, inputs from a malicious client. Nothing here enters the
certified gate.

**On the owner's machine (2026-10-11).** 0198 and 0199 applied as trees `72856a08…` and `936c5054…`, as predicted.
`bot_ref.py make tactical`, twice: the same file (`fc /b`: no differences), digest `a75baf13…`, sha256 `0ff71da1…`, the
same as in the container. `check`: `BOT TRACE CHECKED`. `compare` against his Firefox 157's own trace, whose walk its
own bot recorded: the start, every input and every state the same, field by field, 1,787 ticks. Then Firefox 157 and
Edge 155 played the Python walk (`trace.py run --inputs graybox/build/bot/tactical-walk.json --browser firefox` and
`--browser msedge`, each accepted as its family): `compare` against each, the start, every input and every snapshot
the same as the Python tick's; `tick_ref.py verify` on each, VERIFIED; `trace.py compare` of the two, cross-engine,
under rules 1 every state the same at every tick, and under rules 0 `Math.cos` different on 1 of 678 common
arguments and `Math.hypot` on 255 of 677, with every state still the same. The self-test on his Firefox's trace:
`BOT-REF SELFTEST PASSED`, every row as in the container, and the note on the platform's atan2 again found at tick 519
(his Windows C library, as the container's Linux one). The gate 251 rows / 0 fail; pushed `514a45e..4f0ab5c`.

So, in his acceptance table: the bot deterministic, MEASURED here and on his machine; the reference tick right for
the Python walk, MEASURED in four engines (Chromium 141 and node 22 in the container, Firefox 157 and Edge 155 on his
machine); the browsers' agreement with Python on Python-originated inputs, MEASURED in those four; the bot's intended
behaviour, held by its invariants and plants, with four choices this walk does not exercise.

**His ruling.** *"ACCEPT BOT-REF-0 provisionally."* *"The four untested policy choices matter: they remain
unspecified by evidence, even if this particular walk is stable."* And of the gate: *"These additions are outside the
certified gate, so this does not establish that the gate itself covers their behavior."*

### INPUT-CONTRACT-0 — the tick's input admitted or refused, whole · **the owner's ruling** (2026-10-11); outside the certified gate · **built** (`graybox/RULES-1.md` *The input*, `graybox/web/input_cases.json`, `admit` in `graybox/web/sim.js` and `graybox/tick_ref.py`)

**His ruling.** *"I agree with the proposed hostile-input slice, with one adjustment: make it a shared input-domain
contract, not an attempt to force every invalid input through the same error mechanism accidentally."* First the
domain, in `RULES-1.md`: the fields and their types, finiteness, bounds, the pitch's non-finite values, booleans,
missing and unknown fields, *"validation timing: validate the complete tick input before mutating authoritative
state"*, *"one canonical rejection category for each invalid-input class"*. *"For accepted inputs, rules 1 should
preserve bit-identical tick semantics. For rejected inputs, require equivalent contractual outcomes—same rejection
category and no state mutation—not identical exception text or stack traces across Python and JavaScript."* On the
non-finite turn: *"My recommendation is to reject non-finite turn inputs before the tick starts. This keeps NaN out of
authoritative state, where cross-engine bit identity is not a sound contract. Do not broaden this into a ban on every
large finite number unless the intended input policy requires it."* A matrix of cases, *"Test both implementations
against the same table. Include mutants that validate after mutation, accept NaN, and silently ignore an unknown
field."* *"Do not fold network security, packet framing, rate limiting, or server authority into this slice."* His
acceptance criterion: *"every input class has a written disposition; JavaScript and Python agree on acceptance or
rejection; rejected inputs cannot partially mutate state; valid inputs continue to match the rules-1 reference tick."*

**Before it, measured on the code as it stood.** The table's 61 steps that must now be refused, played through the
old `sim.js` (node 22) and the old `tick_ref.py`: JavaScript ran 54 of them and threw on 7, Python raised on 20, and
every one changed the state in both, at least its count of ticks, even where it threw (a side `"C"` failed in the
spawn after the count had moved). On 13 one implementation ran where the other raised; on 7 more both ran and ended in
different states. An infinite turn made JavaScript's yaw NaN (its bits `fff8000000000000`) for the rest of the run
and Python raise a `ValueError`; a turn written as the string `"0.5"` was joined to the yaw as text in JavaScript (NaN
after the wrap) and taken as 0 in Python.

**The dispositions** (`RULES-1.md`, *The input*): a record (a plain object, a `dict`) whose own fields, in the order
of their names by UTF-16 code units, are flags `true` or `false`, a side `"A"` or `"B"`, or a finite turn; anything
else refused with the category of its first fault (`INPUT-NOT-RECORD`, `INPUT-UNKNOWN-FIELD`, `INPUT-FLAG`,
`INPUT-SIDE`, `INPUT-NUMBER`, `INPUT-NOT-FINITE`), the state untouched; the tick reads the admitted copy, not the
record again. His matrix, row by row:

| his case | disposition |
|---|---|
| `dyaw` `+∞` or `−∞` | refused, `INPUT-NOT-FINITE`, the state unchanged |
| NaN in every numeric field | refused, `INPUT-NOT-FINITE`: three NaN encodings (quiet, the sign set, a payload), in both fields |
| `dpitch` `±∞` | refused, `INPUT-NOT-FINITE`, not clamped: one rule for every number in an input |
| very large finite turns | admitted, no bound: the yaw reduced by `fmod`, exact for every finite double, the pitch held at ±1.45; the largest double either way, 3 × 10⁶, 2²¹, the smallest subnormal, each ticked to the same state in both implementations |
| a missing required field | no field is required: an absent flag is false, an absent turn `+0`, an absent side leaves the side. Every recorded run relies on that (the fight's idle ticks are `{}`), so the class is empty by design |
| an unknown field | refused, `INPUT-UNKNOWN-FIELD`: `crouch`, `F`, `__proto__`, `constructor`, `toString`, the empty name, `"dyaw "`, `"0"` |
| `true` or `false` in a flag | admitted |
| `0`, `1`, strings or null in a flag | refused, `INPUT-FLAG` (lists and records too) |
| a repeated invalid tick | the same category each time, the state unchanged each time |
| a valid input just after a refusal | the run goes on from the state before the refusal: a run with six refusals among twenty ticks ends where the run without them ends |

And the rest: an input that is not a record, `INPUT-NOT-RECORD`; a side other than `"A"` or `"B"`, `INPUT-SIDE`; a turn
that is not a number, `INPUT-NUMBER`; several faults in one record, the first in the order of names.

**Built.**

- **`graybox/RULES-1.md`**, *The input (contract 1)*: the domain, the categories and their order; the contract
  versioned (1) apart from the rules. The arithmetic table's rows for a flag and a turn now say what an admitted input
  can hold.
- **`graybox/web/input_cases.json`**: 70 cases, 121 steps, each step's required outcome, written in a notation that can
  hold what JSON cannot (a NaN's bits, `−0`, an infinity, a field named `__proto__`, an input that is not a record).
- **`sim.js`**: `admit` before the tick, which reads the record once and passes its copy on; `step` returns `null`
  or the category; `inputCases` and `inputFaults` play and judge the table; the self-test's new check `input-contract`
  plays it, with four records only JavaScript can make (a flag left `undefined`, a `Date`, a record without a
  prototype, a getter, read once) and the four plants. The self-test is 30 / 30 on the tactical map, 27 / 27 on the
  witness level.
- **`sim_worker.js`**: a `cases` mode; and its decoder of a trace's inputs now makes each field an own property. An
  assignment of `__proto__` sets the prototype and loses the field, so a trace input naming it would have been played
  without it in a browser and read with it in Python.
- **`trace.py run --cases`** plays the table in a browser and writes each step's outcome and state;
  **`tick_ref.py cases [RESULTS.json]`** plays it in Python, with the four plants, and holds a browser's results to the
  table and to Python, step by step.
- **`graybox/web/main.js`, `art/web/play.js`**: the live loops build records the contract admits. A key never pressed
  had given `undefined` in a flag, and the graybox sent `side: null` on every tick; now every flag is `true` or
  `false` and the side is sent only when asked for. A refusal is shown once in the console.

**Measured in the build container (2026-10-11).**

- Python: every step as the table requires. The plants: the check made after the tick has begun (63 faults), NaN
  admitted (9), an unknown field ignored (13), a side applied before the rest of the record is checked (2). The same
  four in the page's self-test give the same counts.
- node 22 and Chromium 141 (`trace.py run tactical --cases --expect chromium`): every step as the table requires, and
  against Python every outcome and every state the same, all 121 steps. MEASURED, these two V8s.
- Nothing admitted changed: re-recorded in Chromium 141 after the change, both maps' three runs under both rules,
  every start, input and snapshot the same bytes as before it; `tick_ref.py verify` on both maps; the self-tests of
  `bot_ref.py`, `trace.py`, `tick_ref.py` and `rules_ref.py`; the page's self-test 30 / 30 and 27 / 27; the plaza's
  live tests 13 / 13, and 11 / 11 in the browser; the graybox page played (walking, reset, side B) with no refusal.
- Mutants: ten of `sim.js` and eight of `tick_ref.py`, 15 refused. Three are equivalent and so classified:
  JavaScript's flags tested by `typeof` (the same values pass); Python's names sorted by code point (the orders
  differ only above U+FFFF, and every name with a category of its own is ASCII); Python's tick reading the record
  rather than its copy (a `dict` has no getters; in JavaScript the same mutant is refused by the getter's one read).
  One of the fifteen is refused only across the implementations: JavaScript's admitted copy left empty. Every tick
  then does nothing, alike, so the table alone (outcomes, unchanged states, runs ending together) holds, while
  Python's states part at the first admitted step, and the rest of the self-test fails.

**What it does not show.** His limits: not network security, packet framing, rate limiting or server authority. Not
a hostile caller in the same process (a Proxy, a getter that throws): the contract is on data records. Not
JavaScriptCore; Firefox and Edge are his to run. Not that the table holds every input: it holds the classes he named
and their edges.

**On the owner's machine (2026-10-11).** 0200 and 0201 applied as trees `06541c0a…` and `27c689b2…`, as predicted.
`tick_ref.py cases`: `INPUT CONTRACT HELD`, the four plants giving the container's counts. Firefox 157 and Edge 155
played the table (`trace.py run tactical --cases`, each accepted as its family): 60 steps ticked, 61 refused (`INPUT-FLAG`
11, `INPUT-NOT-FINITE` 17, `INPUT-NOT-RECORD` 7, `INPUT-NUMBER` 6, `INPUT-SIDE` 8, `INPUT-UNKNOWN-FIELD` 12), and
`tick_ref.py cases` held each to the table and to Python: every outcome and every state the same, all 121 steps,
`INPUT CONTRACT HELD BY PYTHON AND THE BROWSER`. His Firefox's own runs recorded again after the contract, against
its trace from before it (`trace.py compare`, the same engine): every call of the engine's `Math`, every input and
every state the same, under both rules; `tick_ref.py verify` on the new trace, VERIFIED, 5,863 ticks. The page's
self-test in his default browser (whose `Math` measured as Firefox 157's had: `sin` different from the rules' on 70,
`cos` 62, `hypot` 693 of 4,000) passed 30 / 30 and 27 / 27, `input-contract` among them with the same four plants'
counts; the plaza's live self-test 13 / 13; the gate 251 rows / 0 fail; pushed `4f0ab5c..714792c`.

So his acceptance criterion holds on the tactical map in four engines (node 22 and Chromium 141 in the container,
Firefox 157 and Edge 155 on his machine): every input class has a written disposition; JavaScript and Python agree on
admission or refusal and on the category; a refused input leaves the state as it was; admitted inputs give the rules-1
reference tick's states. MEASURED, these engines, this table.

### STUDIO-0 — the summonable live director · **the owner's direction and ruling** (2026-10-11); outside the certified gate · **built** (`art/studio.py`, `art/STUDIO.md`, `art/providers/`, the studio in `art/play.py` and `art/web/`)

**His words.** *"The way to streamline this is to make Verðandi feel less like a collection of procedural-generation
scripts and more like a UE5-style world studio where the designer can summon an AI collaborator directly into a
running world."* *"The designer should not have to think about patches, JSON, procedural parameters, or verification
commands."* *"The key design principle: the LLM edits design intent; Verðandi compiles that intent into a live world;
the designer remains in control."* The workflow: load and inhabit a world; select or summon (*"Without a selection,
the prompt applies to the whole world"*); describe the result; *"Summon live alternatives"*, two or three candidates in
the actual world, switched between from one place or walked through; admit, reject or refine, *"Every change has
undo, provenance, and a clear record of what changed. The live world stays playable throughout."* The pipeline:
*"The LLM should not directly rewrite the live scene or produce arbitrary engine code for every request. Give it a
constrained, structured editing interface"*; designer intent, an AI design proposal (*"Target, desired effect,
constraints, scope, candidate edits"*), the scene compiler, a preview in the running world, the designer's admission.
The behaviours: keep playing while generating; preview transactionally; preserve session state; control edit scope;
prevent stale results; undo at the intent level; keep the interaction direct; *"The exact latency target should be
measured against real candidate complexity rather than promised universally."* What to build first, in his order:
the live viewport and the summon; multi-candidate comparison; selection, hierarchy and property overrides; revision
history and scope-preserving edits; visual-quality feedback. *"My recommendation: make the next milestone a
summonable live director, not another verification rung. Start with the current plaza, object selection, a prompt
panel, three candidates, live preview, and admit/reject/undo."* *"The test of success is simple: can a designer make
a meaningful, high-quality change to a running world faster by describing it than by manually constructing it?"*

**Its place in the order.** His ruling of the same day puts INPUT-CONTRACT-0 first: *"After that, return to the art
loop"*, *"The plaza candidates should not remain indefinitely blocked behind verification work."*

**What exists for it already** (NATIVE-PLAZA-0, DIRECTOR-0): the plaza played in the browser with the graybox's
simulation; an edit to an intent compiled in a fresh process and swapped into the running page only when it compiles
(the game, its position and inputs kept; a refused edit leaving the scene as it was); candidates checked against the
head they meet and admitted or refused by a person, every step in an append-only ledger. **What does not:** a
selection in the page, a prompt panel, a model that writes a structured proposal, candidates made from one prompt and
compared in place, and admit, reject and undo from the page.

**His ruling on the model (2026-10-11).** Asked which model the director should call, he chose *"a pluggable model
adapter, with a persistent local director service behind it. Keep the studio independent of any particular model"*:
*"a local director gateway that accepts requests from `play.py`, invokes a configurable model provider, validates its
output, and returns up to three structured design candidates. Start with a CLI adapter so the first implementation
remains standard-library-only; add direct API adapters when useful."* *"The key architectural decision is that the
model proposes changes—it never directly mutates the live world. Verðandi owns validation, compilation, preview, and
admission."* What makes it robust, in his list: structured output (*"Where supported, use the provider's constrained
structured-output feature rather than relying on prompt instructions alone"*); *"Safe process boundary: Pass the
prompt and context through stdin or a request file, never concatenate user text into a shell command. Limit output
size, execution time, and concurrent requests"*; stale-result protection by request ids and source revisions;
graceful failure; *"Credential isolation: API keys stay in environment variables or an appropriate local secret
store; never expose them to browser JavaScript"*; *"Reproducibility: Record the provider/model identifier, prompt,
context revision, candidate output, and compiler result. Replaying a recorded candidate should not require another
model call."* *"A single configured CLI process is sufficient for the first version."* *"I would not make 'Me, in
Cowork' the primary runtime dependency."* His acceptance test: *"press the summon key, enter a prompt, receive up to
three valid candidates, preview one without resetting the player, reject a malformed candidate safely, cancel a stale
request, and keep the world playable when the model is unavailable."*

**Built.**

- **`art/studio.py`, the gateway**, inside `art/play.py`. For a request (the prompt, the selected piece, the camera)
  it reads the head as the files stand and writes one `VERDANDI-STUDIO-REQUEST 0`: the id and the head, the selection
  with the brief's statement that made the piece (line, text, key) and its address patterns, the camera, every
  statement of the brief, the revision syntax, the art language's reference (from `art/README.md`) and the response's
  JSON Schema. A provider is a command from a configuration (an argument list, no shell), given the request on its
  standard input, limited in time and in output, killed when the designer cancels or a newer request supersedes it.
  Its `VERDANDI-STUDIO-RESPONSE 0` is read whole or refused whole (`STUDIO-RESPONSE-*`): the request's id, at most three
  candidates of five bounded fields (a title, a rationale, revision lines, a scope, what it means to keep). Each
  candidate becomes a `VERDANDI-INTENT` (the letter, the base and the prompt the gateway's) and the director evaluates
  it at the current head; one it refuses is shown with the reason and never drawn, the others are compiled and served
  as sources. Admission evaluates the candidate again at the head as the files stand and admits it through the ledger
  only if that is the head it was drawn at and it is CLEAN; rejection records an evaluation and a refusal; undo admits
  the latest admission's exact inverse as an intent of its own (an undo is never undone; undo again walks back). Every
  request is recorded under `art/build/studio/` (the request, the raw response, each candidate's intent, one log line
  with the head, the provider, the model, the prompt and the outcome), and a recorded candidate plays again without
  the provider (`play.py --intent …/A.intent`).
- **The page** (`art/web/play.js`, `play.html`): E selects the piece of the dressing under the crosshair (the nearest
  box the ray meets; a wall in front hides it), and a frame marks it on screen; Enter opens the panel (the game goes
  on, and typing is not playing); Ctrl+Enter asks; each candidate with its verdict and Show, Admit and Reject;
  Original, Undo and Cancel. Show switches the drawn source as `[` and `]` do: the same map, so the scene changes and
  the game, the player and the camera do not.
- **`art/play.py`**: `--director CONFIG.json`; `--root DIR` (the brief and ledger of another tree, as the self-tests use);
  `/studio/piece` and the five POSTs (ask, cancel, admit, reject, undo), each carrying the token the page is served
  with and naming 127.0.0.1 or localhost (as built at STUDIO-0; STUDIO-1 replaced `/studio/piece` with the
  `select`, `pin` and `unpin` POSTs, eight in all, `art/play.py:432`); the studio's state in `/live`. Without `--director` the panel says so and the
  world is played as ever.
- **The providers** (`art/providers/`): `scripted.py`, which is not a model (three fixed variations of a selected
  canopy, the three of his sketch: *Monolithic*, *Lit underside* with magenta fixtures if the prompt says so,
  *Deeper canopy*; anything else answered with nothing); and `anthropic_messages.py`, Claude through the Messages API,
  its key and model in the environment, given one tool whose input schema is the gateway's and made to call it.
- **`art/STUDIO.md`**: the contract (the configuration, the request, the response, every refusal's code, what is kept,
  the boundary, what is not shown).

**Measured in the build container (2026-10-11).**

- `python art/studio.py selftest`, 29 / 29, in a scratch copy of the brief, its ledger and the maps: the scripted
  provider's three candidates CLEAN and drawn on the same map in 0.4 s; the request recorded, and a recorded candidate
  replayed without the provider to the same scene; a POST without the token, or naming another host, refused (403);
  A admitted through HTTP (the ledger's evaluate and admit, the page's source 0 the candidate, the ledger verifies);
  B, drawn before that admission, refused as stale; C rejected; a second request on A's head and its C admitted; undo
  twice, back to the brief's bytes and scene; the ledger verifies. And each way a provider fails, the world served as
  it was: no provider; a configuration with a shell line; not JSON; another request's id; four candidates (refused
  whole, not cut to three); a candidate that names no statement (shown, never drawn) beside one CLEAN and one LEAKAGE
  (drawn, not admitted); a cancellation (the command killed before it could write its mark); a newer request (the
  first's result discarded); a timeout; an exit with an error (*the model is unavailable: 503*); output past the limit;
  a command that cannot start; and the Anthropic adapter against a local server answering as the API's documentation
  describes (the key in `x-api-key`, `anthropic-version`, one tool whose input schema is the gateway's, the call
  forced, the tool's input read back as the candidates), an overloaded answer (529) and no key (nothing sent).
- **His acceptance test in a browser** (Chromium 141, headless, through the page's own keys and buttons; a harness of
  the container's, not committed), 10 / 10: E selected the north slab and the frame marked it; Enter summoned the
  director, the prompt typed did not move the player, and three CLEAN candidates came back; B shown in place — the
  scene swapped, the same state object, the player where he stood, the ticks going on, no new game; B admitted
  through the ledger and source 0 became it; undo restored the brief and its scene; a candidate the director refuses
  shown with its reason and Show disabled, the others drawn; a slow request cancelled from the page while the world
  ticked; a provider that fails (503) shown, the scene kept, and W walked the player on; no page errors.
- Mutants of the gateway and its endpoints: 13, 12 refused by the self-test. The survivor is equivalent: dropping the
  check that discards a response that arrives after its request was superseded leaves the second check, before the
  candidates are published, to discard it. Two were refused only after the self-test grew: four candidates (cut to
  three silently, until a provider of four was added) and a LEAKAGE candidate admitted (which had made the director's
  own refusal, a `SystemExit`, drop the connection; the director's refusals are now the gateway's,
  `STUDIO-DIRECTOR-REFUSED`).
- Stills of the brief and the scripted provider's three candidates for the north slab, from one place in the plaza,
  in the build container's software renderer, were sent to the owner; they show the candidates differ, and are not a
  judgment of them.

**What it does not show.** The quality of what a model proposes: the director's checks hold a candidate to the art's
rules and to its declared scope, not to taste. The live Anthropic API (no key in the build container). Selecting a
light or a play piece. A change to the layout (the look only). A long-running worker: each request starts the
provider afresh, which he allowed for the first version. Any latency of a model. Firefox and Edge on his machine are
his to run. Nothing here enters the certified gate.

**On his machine (2026-10-11).** 0202 and 0203 applied as trees bbe88393 and 78c85323, as predicted. On Windows:
`python art/studio.py selftest` 29 / 29 (a command that cannot start said as `[WinError 2]`), the first run of the
gateway outside the build container; the plaza's live self-test 13 / 13; `ART CHECKS PASSED`; `DIRECTOR SELFTEST
PASSED`; the gate 251 rows / 0 fail (rowset 74db4c8d78625af5); pushed 714792c..59861b4. He then played the plaza with
the scripted provider. His studio records (`art/build/studio/plaza-night/`, read in his folder, not copied into the
repository) hold four requests between 22:41 and 22:44 UTC: *"make it look more structurally realistic"*, then three
times *"make it look more structurally realistic with realistic building code design features"*, on three of the
plaza's canopies; each answered in 122–163 ms with the same three CLEAN candidates, since the scripted provider reads
a prompt only for the word *magenta*; *Lit underside* (B) admitted each time (ledger #24 and #25, #28 and #29, #30
and #31, #32 and #33) and the first undone (#26 and #27), the page swapping the scene each time. He restored the brief
and its ledger with `git checkout`. He then started the studio on the Anthropic provider; no request was recorded, so
nothing was sent.

**What he found.** That the words did not change the answers, and *"there is no object bar code or whatever so i can
say match the design of this object or make it look like it connects"*. Both stand on the code as built: the
scripted provider is not a model; the request carries the selected piece's id, but the page never shows it, a second
piece cannot be named, and nothing in metres is sent. And a model would be held to the art language: a canopy has a
height, two corners, a depth, ribs, downlights and edge fixtures, and no statement makes a column, a bracket or a
hanger (a column on the floor would also be refused by the check that no dressing stands where a player can be).

**His rulings (2026-10-11).** On the model: *"Choose “Both, CLI first.” That gives Verðandi two real model paths
without tying the studio to either one"* — Claude Code's CLI, *"first provider to implement and test"*, and the
Anthropic API kept, *"configure it with a Console API key, and compare output quality, latency, reliability, and actual
cost."* *"the CLI route is convenient for your personal development setup, but it is not a substitute for a properly
authorized provider integration in a product offered to other users."* *"A better model cannot invent usable columns
or hangers if the scene language cannot represent them. The model adapter and the scene-authoring language are
separate bottlenecks."* For the CLI provider: *"`--tools ""` must actually result in no available tools. The gateway
must independently validate the returned JSON regardless of the CLI's schema enforcement."* *"The provider's smoke
test should prove that the model was actually invoked—not just that a provider configuration was loaded. Record the
provider, model, exit status, schema-validation result and latency, without logging secrets."* *"Implement CLI first,
API second, shared schema and gateway throughout."* The comparison: *"whether candidates actually reflect the
requested change; whether the scene language can express those changes; invalid-output and timeout rates; latency
and cost per accepted edit"*; *"the best director is not the model that generates the most text or candidates, but
the one that helps the designer reach a good, accepted world edit with the least friction."* On the references: STUDIO-1,
below.

### STUDIO-1 — two model paths, and references: tags, pins, geometry and relations · **the owner's rulings** (2026-10-11); outside the certified gate · **built**

**His ruling.** *"Choose “Tags + pins + geometry” for this slice. Keep the reference system and art-language vocabulary
separate so you can establish reliable object grounding before expanding what the compiler can build."* What it
includes, in his list:

- *"Visible tags: Stable, short IDs such as `@1`, `@2`, `@3` for the current scene revision. Show each tag in the
  viewport and object list."*
- *"Selection and pins: `E` selects the target; `R` pins or unpins references, up to four. Show the pins persistently
  in the prompt panel."*
- *"Metric geometry: For each referenced piece, include its world-space bounds in metres, position, dimensions, and
  orientation. State the coordinate convention."*
- *"Computed relationships: Include measured gaps, relative directions, facing, and nearest relevant wall face.
  Distinguish measured relationships from inferred ones; don't present an approximate facing test as an exact
  connection."*
- *"Grounded prompt context: “Match @2” resolves to the pinned object, with its identity, geometry, and supported
  properties included in the request. The model must not have to guess which object the user means."*
- *"Revision safety: Bind references to a scene revision and object identity, not just a reusable tag. If an edit
  invalidates a reference, report it rather than silently redirecting it."*

Why not connecting pieces yet: *"Adding brackets, hangers, and tie-backs simultaneously expands the authoring language,
exporter, and checks. That makes it harder to tell whether a failure came from bad references or missing construction
vocabulary."* An image of the view is *"the next useful enhancement, not a substitute for the reference contract"*.
His sequence: this slice; then *"Current-view image as optional model context, with a clear fallback for providers
that do not support images"*; then *"Connecting pieces, introduced with explicit attachment semantics and new checks."*
His acceptance criterion: *"the model consistently identifies the intended objects, receives their actual geometry,
and proposes edits the existing compiler can express—without silently changing the meaning of a reference."*

**The reading behind it** (`docs/RESEARCH-FINDINGS.md`, R-14): giving every object a short identifier a model and a
person both use (Chat-Scene), and turning spatial relations into explicit, checked constraints (SceneCraft,
ScanEdit). Nothing of it is claimed as new here.

**Built, the providers (2026-10-11), by his ruling on the model (STUDIO-0, above): "CLI first, API second, shared
schema and gateway throughout".**

- `art/providers/claude_code.py` and `claude_code.json`: Claude through Claude Code's CLI, `claude -p`, on the login
  it has. Run from an empty temporary folder, never through a shell: a fixed instruction as its argument, the request
  on its standard input, its own system text from a file, the gateway's schema (`--json-schema`), `--tools ""`,
  `--disallowedTools "mcp__*"`, `--strict-mcp-config`, `--safe-mode`, `--no-session-persistence`, `--permission-mode
  dontAsk`, `--output-format stream-json`. The session's first event is read before its answer: if it offers any tool
  but `StructuredOutput`, claude is stopped and nothing it said is used. Its answer goes to the gateway, which reads it
  whole as it reads every provider's. On Windows only `claude.exe` is run: a `.cmd` or `.ps1` shim needs a shell and
  is refused, with what to set instead.
- `art/providers/director_prompt.py`: the system text and the request rendered as text, which both model providers
  give their models, so that they are compared on the same question.
- A response may say its usage (`provider.usage`: tokens in and out, a cost or null, and where the cost comes from),
  read strictly. Every call's log line now holds what he asked for: the provider and model the response names, the
  exit status, whether the response was valid, the provider's time, the usage. play.py prints one line a request.
- A cancelled or superseded provider is killed with everything it started (its process group on POSIX, `taskkill /T`
  on Windows), and play.py, stopping, kills a request running: a model's own command line cannot outlive the request.
- `python art/studio.py probe CONFIG.json`, his smoke test: two different prompts about one canopy, through the
  gateway, nothing admitted; SHOWN only if the provider reported a model and tokens for both and the two were answered
  with different revision lines. `python art/studio.py report`: by provider, the requests answered, invalid outputs,
  timeouts, provider errors, the provider's time, the verdicts, the admitted edits, the tokens and the reported cost
  per admitted edit.

**Measured (2026-10-11, the build container).**

- **His check on `--tools ""`**, run before the provider was written (Claude Code 2.1.296): with `--tools ""` and
  `--safe-mode`, the session still offered 22 tools of an MCP server the container connects (its source "dynamic");
  `--strict-mcp-config` did not remove the server; with `--disallowedTools "mcp__*"` it offered `StructuredOutput`
  alone. So the provider passes all three and refuses any session that offers more. With its own system prompt and
  the MCP tools gone, a trivial call's input fell from 15,545 tokens to 3,672.
- `python art/studio.py selftest` 38 / 38: the 29 rows before, and a provider's usage that is not counts refused; a
  cancelled provider's own child killed with it (it would have written a mark 2 s later); every call's exit status,
  validity, time and usage in the log, and no key in it; and Claude Code's CLI through a stand-in for `claude`: the
  flags, the schema, the system text, the prompt on standard input and nowhere in the arguments, an empty folder, the
  model and usage it reported recorded, a line printed; a session offering `Bash` and an MCP tool stopped before it
  could answer; a fifth field in its structured output refused by the gateway itself; out of structured-output
  retries; not logged in; a `.cmd` shim refused with nothing run.
- 14 mutants of the gateway and the provider, 14 refused (among them: only the provider killed, not its group; a
  session's extra tools accepted; no `--disallowedTools`; the prompt in claude's arguments; claude run from the
  repository; a superset of a candidate's fields accepted; the exit status, the usage or the validity not recorded).
- **The probe against the real CLI** (`claude_code.json`, Claude Code's default model, reported as
  `claude-sonnet-5-5`), on the north canopy (`canopy:19,10-28,11`): SHOWN. *"make it read as one heavy, monolithic
  slab that fills more of the sky"*: 16.7 s, 7,780 tokens in, 1,968 out, ~$0.051 by Claude Code's own estimate, three
  CLEAN candidates (the slabs thickened; one slab over the whole plaza in place of three; a heavier material at one
  height). *"make it lighter and thinner, with a warm glow along its edge"*: 15.1 s, 7,783 in, 1,789 out, ~$0.038,
  two LEAKAGE (a material changed without declaring it) and one CLEAN. The scripted provider's probe: NOT SHOWN (no
  tokens; the same lines for both prompts), as it must be.
- **What the probe shows before the references.** One canopy was selected and the prompts said *it*; four of the six
  candidates changed the other two canopies as well (all three of the first prompt's, the third of the second's),
  each within a scope it declared, so the director passed them. The director holds a candidate to what it declares,
  not to what the designer meant: naming the intended pieces is the references' work.

**What it does not show.** The live Anthropic API (no Console key in the build container). Claude Code's CLI on
Windows. Whether a model's candidates are good. A model's latency or cost elsewhere: two calls, one machine, one
model.

**Built, the references (2026-10-11), by his ruling: "Tags + pins + geometry".**

- **`art/studio_refs.py`**, pure functions over a scene. An object is a box of the dressing with its parts (an id that
  extends another by `:something`: a canopy's ribs, downlights and edge fixtures, a tower's cornice) and the lights
  that share their ids; its identity is its id, which holds its cells. Its geometry: bounds, centre and size in metres,
  underside and top, long axis, *"axis-aligned boxes; no rotation"*, its boxes and parts and lights, and, where its
  lights record a direction, which way it faces (measured, as the scene records it). Its nearest wall of the play
  geometry: which, on which side, how far in plan and in space, its top. Between two objects, measured from their
  boxes: the gap (the least distance between their boxes, not their bounds), whether they touch, their overlap in
  plan, the direction and distance between centres, the differences of undersides and tops, whether they share a
  kind, a material, a statement, with the words *"a gap of 0 means the boxes touch or overlap, not that they are
  joined"*; and, where the first faces somewhere, whether it faces the second, marked *inferred* (*"a half-space test
  on centres; not a line of sight, not a connection"*). What a revision of each verb's statement can change, and how
  many objects that statement makes.
- **The gateway** (`art/studio.py`): E (`/studio/select`) makes an object the target, R (`/studio/pin`) pins one or
  unpins it, up to four (`/studio/unpin` from the panel). Each object gets a tag the first time, `@1`, `@2`, …, that
  names it by its id for as long as play.py runs and is never given to another; selecting or pinning it again binds it
  again to the scene and head of that moment. Its status in `/live`, read against the scene served: ok, changed, gone.
  A request (`VERDANDI-STUDIO-REQUEST 1`) carries the target and the pins with their statements, geometry, nearest
  walls and binding (changed since or not), the relations between every two, the tags the prompt mentions, and the
  coordinate convention. A prompt naming a tag that is neither the target nor a pin, or a tag whose object is not in
  the scene at the head, is refused before anything is asked (`STUDIO-REFERENCE`); the target pinned, a fifth pin,
  likewise (`STUDIO-REFERENCE`, `STUDIO-PINS`). Each candidate is shown with what it touches, from the director's own
  verdict (what it realized, and what a changed material affected): each tag changed or not, the untagged objects of
  the head it changed, the objects it made that the head has not.
- **What a model is told** (`director_prompt.py`, both model providers): each tagged object with its line, what its
  statement can change and how many objects it makes, its bounds, its nearest wall; the relations; and, in the system
  text, *"A tag means that object and no other. Change the target; change a pinned object only if the prompt asks for
  it"*, and that a candidate should name the tags it changes.
- **The page**: what is under the crosshair is named in the corner, by its address and its tag if it has one; each
  tagged object is framed and labelled on screen (the target amber, a pin dashed blue); the panel lists the target and
  the pins with their addresses, sizes and lines, and an unpin button; each candidate says what it touches. R pinned,
  so the game's reset moved to Backspace on this page (the graybox's own page keeps R). The scripted provider answers
  *match @N* with one candidate giving the target the pin's material, height and options.
- `python art/studio.py probe CONFIG --references`: his acceptance criterion put to a model. The north canopy the
  target `@1`, the west and south canopies pinned `@2` and `@3`; four prompts, each naming what is to change; for
  every candidate, which tags it changed and how many untagged objects, against what the prompt meant.

**Measured (2026-10-11 and 12, the build container).**

- `python art/studio.py selftest` 51 / 51: the 38 rows before, and thirteen in a scratch copy of their own: tags made,
  kept and never moved (a rib names its canopy; the target refused as a pin; a fifth pin refused; a pinned object made
  the target and back); the request's bounds, relations and nearest wall recomputed from the scene's boxes; the gap
  between boxes, not bounds (an L of two boxes whose bounds enclose a third, 4 m from it); facing marked inferred; what
  a model is told; *match @2* (the target given the pin's height and options, the pin and everything else untouched,
  and the candidate says so); a candidate changing an untagged canopy, one moving the target's corners (a new object),
  one changing a material (every object of it touched); a prompt naming `@9`, or a tag not in the request, refused with
  nothing asked; an object changed since it was pinned (said in the page and the request, bound again when pinned
  again); an object gone (its tag kept, the request refused until it is unpinned, the new object given a new tag); the
  page's POSTs and `/live`.
- **In Chromium 141**, through the page's own keys (a harness of the container's, not committed), 11 / 11: the address
  under the crosshair named before anything is tagged; E, the target `@1` framed and labelled; the west canopy given an
  edge of light through the studio and admitted; R, `@2` pinned and framed as a pin, the player where he stood; the
  panel's list; *make @1 match @2*, one CLEAN candidate saying *@1 changed · @2 unchanged · no other object changed*;
  shown in place, the game untouched; admitted, `@1` shown as *changed* and still `@1`; undone, `@1` as it was; a prompt
  naming `@9` refused in the page; Backspace resets the game; no page errors. STUDIO-0's acceptance test run again on
  the new page: 10 / 10.
- Mutants of the references: 19, 19 refused (a new tag on every touch; a gone object's tag moved to another of its
  kind; mentions not checked; no limit on pins; a part not resolved to its object; bounds from one box; the gap between
  bounds; facing presented as measured; tagged objects counted as others; what a material affected left out; new
  objects not told apart; a change since binding never said; a gone object shown as ok; the target kept as a pin; the
  target pinned; no select endpoint; the scripted match keeping the target's options; the relations not told to the
  model; re-pinning not binding again). The providers' 14 mutants run again on the final code: 14 refused.
- **The references' probe against the real CLI** (its default model, `claude-sonnet-5-5`), each prompt asked twice, 24
  requests in all: about 9,700 tokens in and 800–2,200 out a request, 8.7–17.5 s, $0.014–0.05 by Claude Code's own
  estimate (about $0.64 in all). Three runs:
  - the first, before a candidate's new objects were told apart from the others: 15 of 16 candidates changed exactly the
    tags the prompt named and nothing else; the sixteenth gave `@1` new corners (a shorter slab), a new object by its
    id, which the measure then counted as an untagged object;
  - the second, with that told apart: 16 of 16 as meant (one made a new object, `@1` replaced by a shorter slab); 10
    CLEAN and 6 LEAKAGE, all six the answers to *give @2 a warm glow along its edge*, in one run of it, whose scopes
    named `@2`'s exact address, which does not cover the addresses of the edge fixtures its statement makes;
  - the request was then made to say so beside each reference's patterns (*"an exact address … does not cover the
    parts its statement makes, its ribs and lights"*); the third: 15 of 15 as meant, 15 CLEAN.
  Before the references, the providers' probe (two other prompts, *it* for one selected canopy) had four of six
  candidates changing the other canopies too. The prompts differ, so this is not a measured comparison.
- His key: *"`R` pins or unpins references"*; R was the game's reset on this page, which is now Backspace (said in the
  page and its HUD).

**What it does not show.** That a model identifies the intended objects in general: four prompts, three canopies, one
model, a few runs. The page in Firefox or Edge, or on Windows. Tags on lights or play pieces, tags that outlive play.py
or are shared between pages. A scope pattern for one object with its parts: the director's grammar has none, and the
request only says so; the scope protocol (DIRECTOR-0, its conformance vectors) is unchanged. The image of the view and
the pieces that connect two objects: his next two slices. Nothing here enters the certified gate.

**On his machine (2026-10-12).** 0204, 0205 and 0206 applied as trees 8c4b8777, 82433d43 and d52126f3, as predicted.
On Windows: `python art/studio.py selftest` 51 / 51, among them the first runs outside the build container of a
cancelled provider's own child killed with it (`taskkill /T`) and of a `.cmd` shim refused; the plaza's live self-test
13 / 13; `ART CHECKS PASSED`; `DIRECTOR SELFTEST PASSED`; the gate 251 rows / 0 fail; pushed 59861b4..aa83f2f. Claude
Code was not installed; he installed it (2.1.296, `C:\Users\…\.local\bin\claude.exe`, the official installer),
pointed `VERDANDI_CLAUDE` at it and signed in with his Claude account (`claude auth status`: logged in, `claude.ai`,
his plan). Its default model there answered as `claude-opus-5-5`. From his studio records (read in his folder, not
copied into the repository):

- `probe claude_code.json`: SHOWN. 24.1 s and 21.7 s; about 6,000 tokens in and 2,070 out a request, ~$0.089 and
  ~$0.077 by Claude Code's own estimate; five candidates CLEAN and one REFUSED by the exporter (`ART-REFUSED`: a slab
  0.15 m deep, under the language's least depth of 0.2).
- `probe claude_code.json --references`: 8 requests, 16.8–23.2 s; 20 candidates, 17 CLEAN and each changing exactly the
  tags its prompt named and no untagged object (one making a new object, `@1` trimmed to `@2`'s length); 3 REFUSED by
  the director (`INTENT-APPLY`: a revision naming a statement the brief does not have, each an attempt to change a
  canopy's corners with `=`, when its corners are part of its key), and none of them drawn.
- **The page, in his browser.** A first prompt, *"make @1 match @2"*, was refused before anything was asked
  (`STUDIO-REFERENCE`: the prompt named `@2`, which was not the target or a pin; his target was `@1` and his pin `@4`,
  since a tag goes to an object at its first touch and he had touched two others first); nothing was sent and nothing
  recorded. He also found that the plaza's canopies *"already match"*: all three are the same plain slab, 0.4 m deep,
  and differ only in height and footprint. On a second start: the west canopy the target `@1` and the south canopy
  pinned `@2`; *"give @2 ribs and a warm glow along its edge; leave @1 alone"* (23.3 s, three CLEAN candidates, each
  touching `@2` alone; *Rib every cell, amber edge glow* admitted, ledger #24 and #25); then *"make @1 match @2"* (18.9
  s, three CLEAN candidates, each touching `@1` alone: *Full match: height, ribs and edge light*, *Match the dressing,
  keep @1's height*, *Match height only, no ribs or light*; the first admitted, ledger #26 and #27, the west canopy
  given the south one's height, ribs and edge lights). Both tags then shown *changed since tagged*, as they were.

So his acceptance criterion, *"the model consistently identifies the intended objects, receives their actual geometry,
and proposes edits the existing compiler can express—without silently changing the meaning of a reference"*, held on
his machine for the 23 candidates the director drew (the probe's 17 and the page's 6); 3 more were refused before being
drawn. MEASURED, his machine, his plan's default model, these prompts. And one confusion of use, not of meaning: tags
numbered by first touch are stable, and so not the numbers a designer expects.

### STUDIO-APP-0 — Verðandi Studio, a runnable application that improves itself · **the owner's direction** (2026-10-12); outside the certified gate · **declared; researched and planned**

**His words.** *"The next objective should be a runnable Verðandi Studio, not another narrowly scoped rung. The
reference work is a feature inside that product, and rendered-view context should be batched with other improvements
when the studio workflow can use them together."* *"The shift is from proving individual capabilities to building an
executable application that can continually improve without losing its ability to launch, edit, and play the
world."* Two requirements, not to be conflated: progressive development, and recursive self-improvement, which
*"requires an explicit update and rollback mechanism, not just a prompt that edits source files."* *"Keep the studio
that is running separate from the studio being built."* *"The model must not be able to overwrite the running
executable or promote its own changes without the update supervisor's approval."* *"I would not rewrite the renderer
or introduce Unreal merely to obtain an executable. Packaging is a deployment step; replacing the current rendering
architecture is a separate decision."* *"The existing 251-row gate remains a regression signal, not the definition of
the product."* On scope and method: *"a rung would be a waste on only a simple feature like that... it should be in
a rung batched with other updates"*; *"prioritize larger rungs"*; *"be liberal with custom theorem mixing and be
pioneering. consider ACCT as one of many potential candidates"*; *"when faced with design forks consider producing
both"*. And his intermediary theorem, ACCT (Admitted-Change Containment), proposed *"as a candidate design principle
for the Studio application and update lifecycle—not yet as an established theorem or a new rung."*

**What was done (2026-10-12).** Research first — Windows delivery, process supervision and atomic updates, four
editors, the theory a change transaction composes from, the director's providers (`docs/RESEARCH-FINDINGS.md`,
R-15) — then the inventory from the source, then the decision, then the plan: [`docs/STUDIO-APP.md`](STUDIO-APP.md).
Its consequential decisions: the page stays, in Edge's application mode with a private profile, under a std-only
Rust stub (raw Win32 FFI, as `shell/win32.rs`) that owns a job object and the active-generation pointer and a
std-lib Python supervisor; every version is an immutable generation and promotion is one write-through rename,
blessed by the *previous* generation after a health check; one change transaction (VCT-0, nine parent theorems
mixed, ACCT its statement) with two domain validators, the content ledger and a promotion journal in one canonical
form; five batches, B1 the desktop launch with the content path made crash-safe, B2 the self-change transaction.
Two findings that reorder the first batch: the Messages API provider sends a forced `tool_choice`, which every
current Claude model refuses with 400 (VERIFIED on 2026-10-12; the self-test holds the adapter only to a mock), and
the director writes the brief and appends the ledger without fsync or rename, while the shell's journal does both.
Nothing is built; the gate is unchanged.

**The review (2026-10-12).** 0208 applied as tree 1fc0422a, as predicted; the gate 251 rows / 0 fail; pushed
aa83f2f..2517a27. He then brought three reviews of the plan with one instruction, *"websearch this before
agreement"*. Each claim that bears weight was checked against a primary page the same day (`docs/STUDIO-APP.md`
§13): one review's price claim was wrong (Fable 5.1 is the most expensive model, $10 / $50 per million tokens, not
"cheaper"); the second review's cautions held — `_commit` says nothing of directory entries, no Microsoft page calls
an NTFS rename atomic, process separation is not capability isolation, a generation hash is not a complete cache
key, missing and invalid differ for `??=`; the third review's checkpoint refinement held. The plan was amended: VCT-0
stated as three claims (isolation, promotion correctness, recovery correctness) over an explicit axiom list, with
three levels of consistency claimed apart (process-kill measured; OS-crash under axioms; power-loss not claimed); a
candidate's **basis** (base, sources, validators, toolchain, configuration) recorded at proposal and compared at
promotion, and the only cache key; a generation's integrity verified before activation and recovery, its cost
measured; the capability boundary made real with Windows' Mandatory Integrity Control (candidates validate and are
tried at low integrity, which cannot write the pointer, the journal, the stub or the projects), its limit written;
a fourth experiment for it. The reviews' recommended rulings remain his to make.

**The contract (2026-10-12).** 0209 applied as tree 1d23474b, as predicted; the gate 251 rows / 0 fail; pushed
2517a27..f99c494. He brought a second round of reviews: rulings (Inno Setup *"ACCEPT — optional"*; persistent tags
*"Preserve first-touch numbering and display existing assignments"*; still-image consent *"explicit for each
session"*; the journal-replay court *"ACCEPT — pre-B1 experiment"*; the five experiments *"ACCEPT, conditionally"*;
the default model *"DEFER"* until *"the names, availability, and prices … need current verification"*), the
correction *"Do not let the journal alone determine recovery"* with its question *"At which durable operation does
promotion become committed?"*, and the request for *"a short Studio Architecture Contract that freezes these
interfaces and transaction semantics before B1"*. Done, as `docs/STUDIO-CONTRACT.md`, which governs where it and the
plan differ: the authority of each part; one candidate envelope for content and source (two gaps in the content
domain's found and put in B1: the director's and the scope's source hashes and the configuration's digest are not
recorded); the operations; the promotion journal `STUDIO-TXN 0`, its kinds, writers and grammar; the commit point,
the durable `blessed` record, written by the stub, which no candidate can replace; the tries as `boot` records, so
the pointer is a cache checked against the journal and its rename's atomicity no longer bears on correctness;
`Recover(J, P, F)` as sixteen rules; tags across deletion and projects; the repository contracts the review named,
looked up (all exist; two were misdescribed: BOT-REF-0 is a deterministic bot, HERMENEUTICS-0 is not a source
fence); the five experiments' output form and kill criteria. Its reference, `art/studio_txn.py` (off the gate, no
row), holds the table: `check` over 54 scripted promotions, 41,568 crash states, 195,376 crashes inside recovery,
8,704 chains of failed boots and 134,773 damaged journals and pointers, every rule reached, 0 failures; `selftest`
catches 16 planted wrong decisions and holds a generation's integrity on a real directory (MEASURED in the
container; the stub does not exist yet, and Windows' writes are experiment 5's to measure). The models and prices
were checked again the same day; the default model stays his.

**B1, the first part (2026-10-12).** 0210 applied as tree 5b7923ee, as predicted; on his machine `python
art\studio_txn.py selftest` PASSED (the reference's first run on Windows: the same 41,568 crash states, 0 failures,
the 16 plants caught); the gate 251 rows / 0 fail; pushed f99c494..7234fab (a second `git am` of the same patch,
refused, left a session open, which `git am --quit` closes). He then brought a review with one word, *"agree?"*: stop
the architecture work at the contract (*"Patch 0210 should be the design boundary"*), keep the probes as bounded
prerequisites run alongside B1, take Opus 5.5 for the API provider (*"matching the model already used through Claude
Code"*, configurable), and work by one rule: *"No new architecture proposal, theorem, verification rung, or
candidate-design patch unless implementation exposes a concrete defect that the current contract cannot handle."*
Agreed. Built, off the gate (MEASURED in the container): the content path made crash-safe (`art/director/durable.py`;
an admission writes its old and new files to a pending folder, then the admit event, the commit, then the files;
every director command and play.py's start recover first; `python art/director.py crashtest` kills a real admission
at each of its 10 death points (a torn admit line among them) and once inside a recovery, 14 cases in all, each back
at the parent or the child with the ledger verifying); the tags kept in `art/ledger/<brief>.tags.json` and shown as chips that a click puts into the prompt, a
refusal naming what a tag is and how to pin it; the API provider on structured outputs, `claude-opus-5-5` from its
configuration, a refusal or a cut answer said and not read, the self-test's mock now refusing the old forced tool
choice as the API does; each request's basis recorded (the validators' and the configuration's sha256s, the two gaps
the contract found); play.py's `/healthz`, `/studio/alive`, `/studio/shutdown`, signals and exit codes, `--root`
forwarded to its `--emit` child, its port bound exclusively on Windows (where SO_REUSEADDR *"allows a socket to
forcibly bind to a port in use by another socket"*); the page's heartbeat; the five probes under `tools/probe/`
(probes 3 and 5 also run here on Linux: 50 killed pointer writes all whole; 200 killed promotions, every decision the
contract's). The self-tests: STUDIO 57/57, LIVE 17/17, DIRECTOR SELFTEST and CRASHTEST PASSED; in a browser (not
committed) 11/11 for STUDIO-1's flows and 8/8 for B1's (the heartbeat heard, the chips, an admission through the
crash-safe path, the tags back after the studio was killed and started again). Not yet: the supervisor, the stub, the
layout and the shortcut, after probes 1 and 2 on his machine; the live API (no key here).

**B1, the second part (2026-10-12).** 0211 applied as tree a3b18b17, as predicted; on his machine `python
art\director.py crashtest` PASSED, 14 of 14 (the first run of the MoveFileExW write-through path and of `_commit` on
Windows: every admission killed at a death point recovered to the parent or the child); the gate 251 rows / 0 fail;
pushed 7234fab..30fe6ef. The probes: 2, the job object, HELD (nested in his shell's own job, `AssignProcessToJobObject`
succeeded and play.py, a provider and its child were gone 0.2 s after the job closed); 1, Edge in application mode, HELD
on its kill criterion (pointer lock engaged, W A S D walked, E framed the canopy: his answers, twice) with one case
BROKEN twice, as the plan foresaw: Edge's process was still running 20 s after the page's last heartbeat, so closing
the window does not end the browser. Built, off the gate: `art/studio_app.py`, the supervisor, which joins a job of its
own so that play.py, the provider and Edge end with it; starts play.py on a free port without a console; opens Edge
with its own profile; stops on the page's goodbye beacon (`pagehide`, not followed within 3 s by the page speaking
again, as a reload does), on three minutes of silence (a minimized window's timers slow to about one a minute), or on
play.py's end; opens another window when started twice; says its errors in a dialog and a log; and `shortcut`, which
makes the desktop icon. `/studio/bye` in play.py; the page's beacon; Claude Code's native install found without
`VERDANDI_CLAUDE`; probe 1's `--job` case (Edge started in a job, every one of its processes gone when the job closes).
MEASURED in the container: STUDIO APP SELFTEST 7/7 with a stand-in browser that outlives its window (a reload, a
second start, a silent page, a page that never speaks, play.py that cannot start or is stopped elsewhere), its two
plants caught (the lingering window left running; a reload taken for a close); LIVE SELFTEST 18/18. Moved to B2's
first step: the stub and the layout of generations (B1's one generation is his checkout; *"The studio does not need its
self-updater to update itself in B1. That is B2."*). Not yet measured: the icon on his machine, Edge inside the job.

**B1 accepted (2026-10-12).** 0212 applied as tree 35dd9fff; every self-test passed on his machine; the gate 251
rows / 0 fail; pushed 30fe6ef..02aedc4; probe 1 `--job` HELD; the shortcut made. Then, in his words: *"I ran it from
the desktop icon and it worked as built. congratulations. movement worked and the requested changes held after closing
and reopening the program, as well as the @1 @2 and @3 tags."* His supervisor's log said `processes left in the job at
exit: 256`, a misreading of the job's process list (the structure's two counts read as one pointer-sized word), not
256 processes. Known limitation, deferred: an object's id carries its cells, so an admission that moves or resizes a
tagged object leaves its tag "gone" rather than following it.

**B1 hardened: the ghosts searched for, and fixes 1 and 8 (2026-10-13).** He asked to *"websearch for ghosts to harden
in this before continuing"*. The search (fencing tokens, crash consistency, fsync errors, hash-chain freshness, event
and cache-key drift, pinned stores, DNS rebinding, browser throttling and sleeping tabs, job objects, queues that pay
twice, the configuration complexity clock, mode collapse, physics determinism) was checked against the source; eight
ghosts were found live, each graded, and the fixes ordered. His review: *"Go — with three amendments worth making
before the commits start"*; *"Fix 1 must fence inside the callee, not the callers"*; *"Fix 1 needs its own recovery
rule, or it becomes a deadlock"*; *"Fix 8 can ride with any commit."* Two further amendments were found by reading and
measuring, and he approved them: *"Approved. Both amendments are stronger than the original plan, and the measurements
back them up."* — the lock belongs to the store, the ledger, since two threads appending to one ledger broke its chain
in 19 of 20 trials (MEASURED in the container); and recovery refuses rather than clears, since every director command
and every start recovered, and so could undo an admission still alive in another process. His addition: *"When
releasing the lock on error, remove the `.pending` folder you created before raising the exception."* His order:
*"Proceed with Fix 1 + Fix 8 in the same commit."* Built, off the gate: the content lock (`art/director/durable.py`
`locked`; `art/director/ledger.py` `lock_path`) — a thread lock in a process and the system's file lock between
processes (msvcrt.locking, flock), released by the system when its holder dies, so no timeout ever takes it from a live
holder — held by every ledger append from its read to its append, by every admission from before its first write to
after its last, by the tags file's write, and by recovery, which waits (60 s, `VERDANDI_LOCK_WAIT`) and then refuses
(LEDGER-BUSY) having changed nothing. One lock for a whole tree, not one for each ledger: the briefs, ledgers, tags and
maps of every brief share their folders, and recovery sweeps them, so a lock of one brief would let it remove another
brief's temporaries; it also serializes two worlds' writes of a shared map. The fence: under the lock an admission
computes the head again from the files and refuses (HEAD-MOVED) if it is not the head its caller checked; every caller
of `commit_admission` is fenced there. An orphan pending folder met by an admission under the lock is recovered first.
On a failure, a pending folder is removed only if its manifest was not yet written; once it was, the folder is that
admission's redo and undo, and it is finished at once under the lock instead (removed blindly, an admission whose
event was written would be left half installed). Found while building it and fixed with it: `Workspace.export` points
the module-global `level.MAPS` at the folder it reads, and two exports at once (the brief's maps and a candidate's)
failed on the first try (MEASURED), so exports take one lock; the gateway's `quiet()` swaps the process's one standard
output, and two at once left it redirected in 20 of 20 trials (MEASURED), so it takes one lock. Fix 8: play.py answers
a GET, as a POST, only to 127.0.0.1 or localhost by name. MEASURED in the container: DIRECTOR RACETEST PASSED (32
cases: threads and processes appending; exports at once; at each of an admission's nine writes a second admission
refused by the fence or before it, and another process's recovery refusing and changing nothing; a holder that dies
releasing the lock; a failure before and after the manifest; an orphan recovered by the next admission; and the plants
— no lock, 5 of 5 chains broken by threads and 3 of 3 by processes; no export lock, 23 of 40 exports wrong; no fence,
the second admission written over the first; a recovery that ignores the lock, the tree changed under a live
admission), DIRECTOR CRASHTEST PASSED (14 cases), DIRECTOR SELFTEST PASSED, STUDIO SELFTEST 59/59 (a GET by a rebound
name refused; two `quiet()` calls at once, and their plant), LIVE SELFTEST 18/18, STUDIO APP SELFTEST 7/7, VECTORS
62 / 62, ART CHECKS PASSED; in a browser (not committed) B1's flows 9/9. Not measured: the lock on Windows (his
`crashtest` and `racetest` will run it; Windows releases a dead holder's lock at a time that "depends upon available
system resources", which the wait absorbs). Next, in his order: 3, 4, 6, 7, 2.

**0213 on his machine, and the self-tests' world (2026-10-13).** 0213 applied as tree b1dedbf1, as predicted. On
Windows `python art\director.py racetest` PASSED, 32 of 32: the content lock measured there for the first time — the
chain whole under two threads and two processes, every plant caught (no lock: 5 of 5 and 3 of 3 chains broken; no
export lock: 9 of 40 exports wrong), the recovery of another process refusing at each of the nine writes, a dead
holder's lock taken back after 0.00 s; `crashtest` PASSED, 14 of 14. `python art\studio.py selftest` failed four rows
(the request's record, a refused candidate shown, the Anthropic adapter and Claude Code's CLI drawing nothing) and
stopped in the references' self-test (`assert west0 + "\n" in text`). Not 0213: the studio's, the references', the
live loop's and the desktop studio's self-tests copied `art/briefs/`, `art/ledger/` and the maps from the checkout, and
his brief and ledger there now hold the edits he admitted through the studio, which the rows' expectations (the
north slab's statement, the west canopy's line, a canopy with no depth yet) were not written for — the defect
DIRECTOR-0's self-test had and lost on 2026-10-10 (its fixture the live state). Reproduced in the container: an
edit like his, recorded by `rebase`, failed four rows of 59 at 0213. Fixed: `art/fixtures/selftest/` keeps the brief,
design and layout as committed when those self-tests were written, and `art/director.py`'s `selftest_tree` lays them
under a scratch root with the graybox's own maps and starts a ledger on them; the four self-tests play there, and a
row says so. With the same edit in the checkout: STUDIO SELFTEST 60/60, LIVE SELFTEST 18/18, STUDIO APP SELFTEST 7/7
(MEASURED in the container).

**0214 on his machine (2026-10-13).** 0214 applied as tree 9365b09b, as predicted; the fixture row passed and with it
the four rows his working brief had broken, and the references' self-test ran to its end. One row failed and the
summary then stopped: *"a newer request supersedes the one running: its result discarded — the first ?"*, and
`sum(rows)` met a list — the row's `... and first_out and ...` was `[]`, appended as the row's verdict. Two defects in
the test and one in the gateway, fixed: a row's verdict is now `bool(ok)`, so a FAIL is counted and the summary
printed (in the three self-tests that keep rows this way); the row waits up to 30 s for the first request's own
record, which its thread writes only once its provider's tree is dead (on Windows by taskkill, which can come after
the second request is done), and says how long it waited; and the gateway's `requests.jsonl` is written one line at a
time (`studio.LOG_LOCK`), since the request's thread, a superseded request's and the page's decisions record there
at once, and an append on Windows is the C runtime's seek to the end and then a write (git for Windows' fix for the
same: *"Windows does support atomic O_APPEND semantics using the file access mode FILE_APPEND_DATA"*) — two at once can
land on one offset, the later line over the earlier. Which of the two lost his row's record is not known; a new row
records 200 lines from each of two threads and, beside its verdict on the locked writes, says what this machine's
unlocked appends do (MEASURED there, not judged; atomic here). MEASURED in the container: STUDIO SELFTEST 61/61,
LIVE SELFTEST 18/18, STUDIO APP SELFTEST 7/7.

**0215 on his machine, and fixes 6, 7 and 2 (2026-10-13).** 0215 applied as tree 0bf50422, as predicted; STUDIO
SELFTEST 61/61 on Windows, the supersede row passing with its record "after 0.0 s more"; the gate 251 rows / 0 fail;
pushed 02aedc4..3b7d0a9 (0213, 0214, 0215). The new row's measurement on his machine: two threads appending to one
file without a lock kept **399 lines of 400, 396 of them whole** (MEASURED; on Linux 400 whole) — the C runtime's
append on Windows loses and tears lines written at once, so every log written by more than one thread holds a lock
(the ledger the content lock; the gateway's record its own; the queue's, with STUDIO-2, its own). Asked where the
studio's worlds should live — they are files of the checkout, so his edits show in `git status`, could collide with a
patch and could reach the public repository — he chose *"Per-user folder (Recommended)"*:
`%LOCALAPPDATA%\VerdandiStudio\worlds\<name>\`, his plaza moved there as the first world (copied, its ledger
replayed before it is used, the checkout's files never deleted), the checkout's committed plaza the template a new world
starts from; built with STUDIO-2. Then, in his order, fixes 6, 7 and 2, off the gate. Fix 6: `art/studio_app.py`
reads JOBOBJECT_BASIC_PROCESS_ID_LIST as Windows lays it out — two DWORD counts, then pointer-sized ids (B1 read an
array of pointer-sized words, took the first id for the count, and logged 256) — and grows its buffer until the list is
whole (*"If this number is less than NumberOfAssignedProcesses, increase the size of the buffer"*); a list that cannot
be read is said. Fix 7: play.py's `/healthz` says `busy` while a request runs, and the supervisor does not take
silence for a closed window while it is: it waits for the request, says so once, then stops for the silence (Edge's
sleeping tabs freeze a background page's timers; whether a minimized studio window sleeps is still not measured); a stop
that leaves a request running says so. Fix 2: a layout admission is refused (SHARED-MAP) while another brief of the tree
plays the same map, in `commit_admission` under the content lock, so every caller is held to it; the refusal says what
to do; an art admission is not affected. The director's own tests now lay the round's base brief alone, not the
checkout's other briefs. MEASURED in the container: DIRECTOR SELFTEST PASSED (with three new cases: a layout refused
while a second world plays the map, both worlds' heads unchanged; an art change admitted, the other world's head
unchanged; and the plant, no check, under which the other world's head moved though nothing was admitted there),
STUDIO APP SELFTEST 10/10 (the process list read from planted bytes, 64- and 32-bit, a cut list known to be cut, B1's
reading of the same bytes giving 256; a silent page while a request runs, the studio waiting for it; the plant, silence
taken for a close, the studio stopping with the request running; on Windows an eleventh, a live job's list),
DIRECTOR RACETEST PASSED (32 cases), DIRECTOR CRASHTEST PASSED (14 cases), STUDIO SELFTEST 61/61, LIVE SELFTEST
18/18, VECTORS 62 / 62, ART CHECKS PASSED; in a browser (not committed) B1's flows 9/9.

**0216 on his machine, and CWCT written (2026-10-13).** 0216 applied as tree ff0d4a9b, as predicted; on Windows STUDIO
APP SELFTEST 11/11 (the eleventh, a live job's list, exactly the process and its child) and DIRECTOR SELFTEST PASSED
with the shared-map cases; the gate 251 rows / 0 fail; pushed 3b7d0a9..15901d6. B1's fix list is done but for the
queue's two, which go with STUDIO-2. Then, in the agreed order, `docs/CWCT.md`: the Creative World Closure Theorem as
he ruled it on 2026-10-12 — *"ACCEPT the Creative World Closure Theorem as the organizing research hypothesis. DEFER
any claim that it is proved or novel."* — and stated as he asked, *"state the l99 version of the theorem in the docs
plainly"*: eight clauses in plain words (nothing reaches a world but an admission, or is found; what is not admitted
changes nothing; an interrupted admission ends at the parent or the child; a late answer never overwrites newer work;
one world's admission changes no other; every admitted state explained by digests; no machine admits; work reaches a
decision, conditionally), with the review's corrections (the box over failures, not admissions; recovery as an
enumerated set; VCT-0's operators imported verbatim; `ProtectedState` defined; `CWCT ⊃ VCT-0`, the content ledger its
content-domain instance; `◊Decided`; shared assets as pinned revisions; a batch and a kill criterion per clause; the
proposal's integrated experiment attached to batches; hash chains with cross-references by digest), the fault model
and the rules the measurements gave, the four operational invariants with their status, the game-and-physics
consequences, the art reviews' obligations as measurements, and the grammar's guardrails. Its sources are
`docs/RESEARCH-FINDINGS.md` R-16. Docs only; no row, rung, pinned source or oracle file changed.

**0217 on his machine, and STUDIO-2 built (2026-10-13).** 0217 applied as tree 782cbdb9, as predicted; the gate 251
rows / 0 fail; pushed 15901d6..fadeb7b. Then STUDIO-2, off the gate: the immediate milestone of his vision document of
2026-10-12, *"Build a desktop-launched application that can open two saved worlds, switch between them, queue an edit
for either world, and review the resulting candidate without interrupting play."*, with the worlds where he chose,
*"Per-user folder (Recommended)"*. **The worlds.** `play.py NAME --worlds DIR` serves every world in a folder, each a
tree of its own — its brief, its ledger and tags, its own copy of the maps, its requests' records, its content lock —
opened when the page or the queue first asks for it (`Hub`). A folder with no world is seeded from the checkout
(`seed_worlds`): each brief copied whole into a folder made aside, its ledger replayed there, and put in place by one
rename only if it verifies; `SEEDED.json` records what was copied, by sha256. The desktop studio serves
`%LOCALAPPDATA%\VerdandiStudio\worlds\` (`studio_app.py`, `--worlds DIR` to choose another). A second world to start
with: `art/briefs/harbor-day.art`, sunlit harbour terraces at midday on the same graybox, nothing of the layout moved.
**The page.** The panel names the world and lists the others (choosing one loads its page); Duplicate as makes a world
from this one, with its own ledger and maps; the Queue section queues the prompt for any world, with a provider and a
model; the task list shows each task's state, its model and the tokens or cost its provider reported, with Cancel,
Review, Set aside and Queue again; a toast says when a task is ready or failed, in whatever world's page is open.
**The queue** (`art/studio_queue.py`). A task belongs to a world and records its references, its camera, the heads
when it was queued and when it ran, its provider and its model; tasks run in the order queued, at most two at once and
one per world; Review draws its recorded candidates again at the head as it is then (`Gateway.restore`), each
evaluated again, never trusted. Fixes 3 and 4 of the review of 2026-10-13: a torn last line of `queue.jsonl` is set
aside and cut, durably, before the next append; a task the studio stopped under is ready when its world's records hold
its answer, and nothing is asked again. Every append to the queue's file holds its lock (his machine's 399 of 400).
With a maps folder per world, play.py's own compile points the module-global maps folder at the world's, and so it
does that under `EXPORT_LOCK`, as the director's export does: a row compiles two worlds over different maps at once,
each with its own map, and its plant, without the lock, reads across. The gateway takes a queued task's references and provider in place of the
page's, and on Windows starts a provider with `CREATE_NO_WINDOW`, so that a studio started from its icon opens no
console window for it (INFERRED from the flag's documentation; not seen on Windows yet).

In a browser (headless Chromium, not committed): the STUDIO-2 flows 10/10 — a target chosen in harbor-day;
plaza-night's page listing both worlds; a prompt queued for harbor-day from plaza-night's page, and the player walking
there while it ran (41 samples with the task running, its provider answering 15 s late); the toast; the task ready,
with Review; Review opening harbor-day with three candidates drawn; an admission there (its ledger two events longer,
plaza-night's as it was); the switcher back to plaza-night; Duplicate making and opening plaza-copy; no page error. B1's flows 9/9 again (its
row on the tags after a restart now waits for the page's first `/live`, which came later than the row looked). Two
findings. A defect of the panel, fixed: after a click on one of its buttons, Esc closed the panel but left the button
focused, so the game's keys went to it and W did not walk (B1's buttons had it too); a closed panel now keeps no focus,
and a focused list takes its own keys. And one of the container, not the product (OBSERVED there only): in headless
Chromium on ANGLE SwiftShader, a navigation away from a page with a live WebGL context did not finish for 40 to more
than 90 s, the server having answered the new document within a millisecond (its request log); with the old page's
context given back first (`WEBGL_lose_context`) the next page was ready in 0.3 s, with software compositing in 3 s
(but a frame then took seconds). The run gives the context back before each click that navigates. Whether switching
worlds is quick in his browser, on his GPU, is not measured. MEASURED in the container: STUDIO-2 SELFTEST 13/13
(seeding, once, a ledger that does not verify refused; each world read by name; a request queued for one world while
the page plays the other, reviewed and admitted there, the other world's bytes untouched; a duplicate; at most two
requests at once and never two in one world, the studio busy while work waits; cancel and queue again; two worlds
compiled at once over different maps, and the plant without the export lock; fixes 3 and 4 with their plants; the
queue read back), STUDIO APP SELFTEST 11/11 (a new row: without `--root` the studio serves its worlds folder, seeded
beforehand from the fixture; with the supervisor made to pass nothing, the row fails), STUDIO SELFTEST 61/61, LIVE
SELFTEST 18/18, DIRECTOR SELFTEST PASSED, DIRECTOR CRASHTEST PASSED (14 cases), DIRECTOR RACETEST PASSED (32 cases),
CONFORMANCE 62 / 62, ART CHECKS PASSED. Not built: a new world from the checkout's committed template after the first
start (the folder is seeded once; a new world is a duplicate). Not held: a studio that dies between asking a provider
and recording that the task started finds the task still queued at its next start and asks again. **His world,
moving.** The studio's first start after 0218 makes the worlds folder from his checkout: his plaza with the edits he
admitted, its ledger and tags (if the ledger verifies in the copy), and harbor-day. Once he has seen his plaza open
from the new folder, the checkout's brief and ledger can go back to the committed ones; the desktop studio does not
read them again, and his earlier requests' records stay in the checkout's `art/build/studio/`.

**0218 on his machine, and harbor-day drawn white (2026-10-13).** 0218 applied as tree e2366170, as predicted; on
Windows STUDIO-2 SELFTEST 13/13, STUDIO APP SELFTEST 12/12 (the new row naming the per-user folder), STUDIO SELFTEST
61/61 (providers started with `CREATE_NO_WINDOW` run and are cancelled as before; whether a console window would have
opened without it is still not seen), LIVE SELFTEST 18/18, ART CHECKS PASSED with harbor-day's checks and plants; the
gate 251 rows / 0 fail; pushed fadeb7b..c925154; and the checkout's plaza put back to the committed one. His unlocked
appends this time: 397 lines of 400, 390 whole (MEASURED; 399 and 396 before). He then played the studio from its icon
and queued a prompt for harbor-day (Claude through Claude Code's CLI, `claude-sonnet-5-5`, $0.0230): *"the director
proposed nothing"*. Two things his window showed. **The answer was empty**, and an empty answer carries no reason;
whatever the model's, the art file has no statement for a person, a vehicle or a prop, so a prompt to add a figure
can only be answered with nothing (art/STUDIO.md says so now). **harbor-day was drawn nearly white**, a defect of
mine: its sun was written as a real sun's 90,000 lux at an exposure bias of −0.6, as Unreal would take them, but the
native renderer is linear in lux, set on the night plaza's moon (0.35 lux at +1.5) with no exposure of its own, so the
sunlit surfaces came out tens of thousands of times the display's white; no check sees a picture, and I had not looked at a still of it
before delivering it. MEASURED in the container (stills, the plaza-centre view): as delivered, 51% of the pixels white;
with the sun at 1.0, 1.6, 2.5 and 4.0 and no bias, none white, a sunlit midday from 2.5 (four more views looked at).
Fixed: the template's sun is 2.5 at no bias; art/README.md says the native renderer's scale; AGENTS.md: a new brief, or
a change to a brief's sky or air, is looked at in a still before it is delivered. His own harbor-day, a world of its
own now, changes only through its ledger: an intent (`harbor-day-sun.intent`, the same two lines, scope `env/light`
and `env/exposure`) evaluated CLEAN and admitted in a seeded copy here, and given to him to evaluate and admit there.

**0219 on his machine, his pivot, and 0220: every request ends in a disposition; the icon opens a first window
(2026-10-13).** 0219 applied as tree c140fe20, as predicted; ART CHECKS PASSED with harbor-day at scene 549d5d76035f;
the gate 251 rows / 0 fail; pushed c925154..b3050b1. In his own harbor-day the sun's intent evaluated CLEAN (ledger #1);
the admit command I gave him failed, `invalid literal for int() with base 10: 'N'`, because it held a placeholder where
the ledger's number goes (my error: a command given to be pasted must be complete; nothing was written, it stopped
reading the number). Then his pivot, toward *"a studio like a mix between ue5 and paint"* with graphics and physics,
researched against his other repositories and the literature (the report was delivered to him, not committed), and
his rulings on what to build: *"The physics layer should enter through the existing exporter, extending
`art/dress.py` so that motion and interaction statements become part of the art language itself"*, and *"the
sequence should be outcomes and launcher, followed by the physics slice"*; and his direction for the icon: *"when i
click the desktop icon a window should open asking what part of the studio should open first; different abstractions
can be added as be design"*. **0220, built, off the gate.** Every request that ends on its own ends in a disposition:
the request publishes the studio's capabilities (what it can make, and by name the closed list of what it cannot make
yet: `entity.person`, `entity.vehicle`, `motion.path`, `motion.surface`, `mechanism.door`, `physics.dynamic`, ...);
the response may carry the provider's `outcome`, and the adapters pass on the API's `stop_reason`; the gateway decides,
the host's observations first: REALIZED, DECLINED (the API's refusal, the studio's decision; or the provider's, with
a reason from a closed list, its account), UNSUPPORTED (no candidates, and what is needed named from the list; a name
the studio has, or one never listed, refuses the response), AMBIGUOUS (one to three questions, shown as text and never
carried out), FAILED (the provider not run or not read, or an empty answer with no reason, `STUDIO-EMPTY-WITHOUT-REASON`);
INFEASIBLE and PROJECTED reserved, no repair stage being built. No disposition but REALIZED evaluates, draws or writes
anything. The request record is hash-chained line to line (`python art/studio.py records`: the chain, the dispositions,
and what was asked for and is not made yet, as telemetry). The queue gains `answered` (a request that came back with
no candidates and a reason: set aside or queued again), and fix 4 covers it (an answer recorded before a restart is
read again, not asked again). The scripted provider names what is missing when a word of the prompt is in its small
list (word matching, said to be). The first window: the icon's URL leads to `start.html`, which lists the worlds, each
read back as it opens (its ledger replayed to its files under its lock; VERIFIED is integrity, not truth; not anchored
outside the world folder, and said so), and six views from manifests in `art/web/views/` (Play and direct, Queue
prompts, History ready; Compose, Mechanisms, Evidence not built, each saying why); a malformed manifest, or one opening
a page outside the studio, is listed as unavailable with why. The window and the History view hold a second token,
good for the heartbeat and goodbye only: they cannot ask, admit or queue. MEASURED in the container: STUDIO SELFTEST
70/70 (nine new rows: each disposition, the API's refusal through both adapters, an outcome naming a capability the
studio has refused, the world byte for byte after every answer without candidates, the record's chain with a line
taken out found and the end cut not, as said), STUDIO-2 SELFTEST 19/19 (the launcher, its token, a broken manifest, a
world changed outside its ledger not verified, an answered task, fix 4 for an answer), STUDIO APP SELFTEST 12/12 (the
window opening on the launcher); in 15 runs of it here, 2 ended a row with exit 1 (the silent page once, the page that
never speaks once), the supervisor's exception not shown, so its cause is not known: the self-test now prints that
exception whenever the supervisor exits 1, and 5 runs since were clean (OBSERVED in the container, not on Windows); the first window and History looked at in headless Chromium at 1100 and 390 px wide. Not
measured: whether Claude Code's CLI passes the API's stop reason on (if not, a refusal on that path reads as FAILED or
as the provider's own account). Next, in his order: the physics slice through the exporter (a platform that carries
the player, a door, a crate, a standing person), which records one rebase in every world's ledger.

**His ruling on the cage, and 0221: QUALITY-0, the scene's bytes exact (2026-10-13).** After the second research
report (on his Dentatus and Ursprung, the creation cage and a quality rung; delivered to him, not committed) he ruled:
*"Remove capability keywords as a pre-model refusal gate."*; *"Four candidate rungs, classified by the host … The
model must not choose its own rung, and filenames alone must not determine it."*; *"A cage around admission, not model
expression."*; *"Every verdict states what it did not check."*; and, refining, *"Classify the effective change, not
only its direct diff"*. His order: *"Run 0220 on your machine first. Then proceed with the exact quality checks,
host-derived rung classification, and mechanically complete verdicts. Defer RULES-2 until those contracts exist."*,
the first of them *"Cheap exact quality checks. Validate finite and bounded scene values, budgets, and stored
reference outputs. Add renderer-independent image checks such as pure-white pixel fraction and other carefully chosen
clipping or black-frame indicators."*, with his conditions that reference images are frozen evidence identified by
digest and that image thresholds are detectors, not proofs. 0220 had not yet been run on his machine when this was
built. **0221, built, off the gate.** `art/quality.py`: every verification (art/check.py, the director's evaluation,
the plaza's serving) now holds the scene's bytes exact — finite JSON in the exporter's one byte form (no NaN, no
Infinity, no number that overflows to one, which `json.loads('1e999')` does without a word, no key twice, no integer
above 2^53 − 1); every field known, with its type and range, restated rather than imported, and a field the checker
does not know refused rather than passed over; every box with extent and inside the world; every coordinate under
1,024 m, where float32 keeps the scene's 0.1 mm steps apart (from 1,024 m, 1,808 of the next 10,000 steps merge); and
inside the native renderer's budgets, read from its own source: it draws the first 160 lights and drops the rest
without a word, and its visibility texture is one texel to a cell, which WebGL 2 guarantees up to 2,048 wide (OpenGL ES 3.0's
minimum as recalled, INFERRED; the specification could not be fetched here, and web3dsurvey.com reports no device
below 4,096, OBSERVED); two
budgets are chosen, not derived (4,096 boxes, 4 MiB). A light above 2,000 cd is noticed, not refused (its glare is
drawn at 2,000). Each checkout brief is held to its frozen reference (`art/references.jsonl`: the scene's sha256 and
each top-level field's, for one art at one exporter); the comparison never writes; `freeze` appends, never twice for
the same inputs, and refuses outright if the same inputs give other bytes. When the exporter changes, the line fails,
naming the fields the new exporter moved, until a person freezes the new references: the golden regression an
exporter change owes. The detectors on stills (PNG, 8-bit RGB or RGBA; anything else is not checked, and says so):
white (every channel 250 or above, and at 255 beside it), black, a channel at 255, distinct colours, mean luma; they
flag and refuse nothing. `approve` reads them on the still it records, and a flagged or unreadable still is approved
only with `--despite-detectors`, which the event records. MEASURED in the container: QUALITY SELFTEST 58/58, each
check against the defect planted for it, and 23 of 23 mutants of `art/quality.py` caught by it; DIRECTOR SELFTEST
PASSED with six new rows (a still approved with its detectors; a mostly white still and an unreadable one refused
without `--despite-detectors` and nothing written, then approved with it and recorded so); ART CHECKS PASSED, both
briefs at their frozen references (harbor-day scene 549d5d76035f, the digest his machine printed for 0219: one
agreement between two machines, OBSERVED); STUDIO SELFTEST 70/70, STUDIO-2 SELFTEST 19/19, STUDIO APP SELFTEST 12/12,
LIVE SELFTEST 18/18, DIRECTOR CRASHTEST PASSED (14 cases), DIRECTOR RACETEST PASSED (32 cases), VECTORS 62 / 62. The
PNG reader agrees byte for byte with PIL's on 21 stills made by headless Chromium, which use filters 1 to 4 (PIL used
here only, as a second reader; not a dependency), and the Paeth predictor it shares with the self-test's encoder is
held to seven answers worked by hand from the specification, so that the two cannot agree on a mistake. The
detectors on those 21 stills: harbor-day as delivered in 0218 flagged, 51.8% white (34.1% at 255) and 66.2% with a
channel at 255; every other still at most 0.34% white and no flag. The thresholds were chosen with these stills in
view: calibration on a handful, not a rate. A correction: 0219's record says *"51% of the pixels white"* without its
definition; it is every channel at 250 or above, and at 255 it is 34.1%. Found, not changed: the art reader takes its
numbers through Python's `float()`, so `2_5` reads as 25, the Arabic-Indic digits six and two (U+0666 U+0662) as 62, and `25e-1` and `+2.5` as 2.5 (MEASURED); a
number grammar of its own is an exporter change, which moves every head, and is proposed to go with the physics
slice's exporter change, one rebase rather than two.

**0222: every verdict complete, the rung computed by the host, the evidence before Admit (ADMISSION-0, 2026-10-14).**
His ruling's third item and the intent half of the second: *"Every verdict states what it did not check."*, *"Four
candidate rungs, classified by the host … The model must not choose its own rung, and filenames alone must not
determine it."* and *"Classify the effective change, not only its direct diff"*. **Built, off the gate.**
`art/director/contract.py` (pure): every evaluation carries a record beside its DIRECTOR-0 verdict, which is unchanged
(VECTORS 62 / 62): the rung, computed from the effective change — the scope protocol's realized and affected
addresses, never the intent's words or its declared scope — A when each is an instance or a parameter of an admitted
kind, C when one is of a kind the classifier does not know, D when the candidate did not export (unknown, classified at
the top); certifies, derived from the checks that ran and passed and the scope's finding; not_checked, every expected
check that did not run and what the director never checks; a horizon of 0 ticks, since nothing in the scene moves; the
sha256 of every component the verdict rests on; and what an admission requires. For rung A that is the verdict CLEAN
(or LEAKAGE accepted), every expected check passed, and a still of the candidate as drawn with its detectors read by
the host, a flagged still admitted only despite them; an undo needs no still, being checked to be the exact inverse of
the admission it undoes. `admit` refuses (ADMISSION-0) until every item is present; an evaluation from before the
record is evaluated again. The still is kept beside the ledger by its sha256, written under the content lock before the
admission's first write; replay refuses an admission of a recorded evaluation without its evidence (LEDGER-EVIDENCE),
and verify reads every still again (LEDGER-STILL). The studio: each candidate's card shows its rung and why, what an
admission needs and what was not checked; Admit takes a still from the canvas (a copy at most 960 pixels wide) and gives
it to play.py (`POST /studio/still`), which reads its detectors; a flagged still admits nothing and shows **Admit
despite**. `python art/director.py record BRIEF SEQ` prints a record; `admit` takes `--still FILE.png`
(`--despite-detectors`, `--inverse-of SEQ`). MEASURED in the container: DIRECTOR SELFTEST PASSED (17 new rows: the
record complete, an admission refused without a still, with a flagged still, and as an undo that is not one, then
admitted as each should be; the evidence and the still read back; three plants on the evidence — detectors that are not
the still's, a still taken away, an admit event written past the director — each refused; a kind the classifier does
not know classified C and not admitted; a candidate that did not export classified D; a skipped check said and keeping
the admission out), DIRECTOR CRASHTEST PASSED (15 cases: one more, death after the still is kept), DIRECTOR RACETEST
PASSED (32 cases), STUDIO SELFTEST 73/73 (three new rows: no still, a flagged still, a still not PNG or without the
studio's token), STUDIO-2 SELFTEST 19/19 (the launcher's token cannot give a still), LIVE SELFTEST 18/18, STUDIO APP
SELFTEST 12/12, STUDIO-TXN SELFTEST PASSED, QUALITY SELFTEST 58/58, ART CHECKS PASSED; in headless Chromium (not
committed) B1's flows 9/9 and STUDIO-2's 10/10 with the still taken by the page, and the card looked at. OBSERVED
there: on SwiftShader the still and the admission took 13 s at 640 × 360 and 122 s at 800 × 450, and `toBlob` waited
minutes for an idle moment the drawing page never had, which is why the page encodes with `toDataURL`; on a real GPU
the time from Admit to admitted is NOT_MEASURED. What is not claimed: that the still shows the candidate (it is bound
by digest; at the command line a person gives it), or that the rung is right beyond the kinds the classifier restates.
For his own harbor-day: an intent evaluated before 0222 is evaluated again before it can be admitted, and at the
command line it now needs a still (`--still`); the studio takes one by itself. Next in his order: the rung of a change
to the program itself, computed by the host (0223), then RULES-2.

**0223: the rung of a change to the program, computed by the host (RUNG-0, 2026-10-14).** The other half of his
second item: *"Classify the effective change, not only its direct diff … calculate the rung from the candidate's
dependency closure and changed semantics, conservatively escalating when that analysis is incomplete."*, and of rung D,
*"a trusted admission path outside the candidate's authority, plus independent evidence"*. **Built, off the gate.**
`tools/rung.py classify BASE HEAD`: the trusted base is anchored by a list of roots (the gate, the art's checks,
QUALITY-0, the director and ADMISSION-0, the admission path and its tokens, the twins and references, the classifier
itself, AGENTS.md), the one place names decide; everything else is computed on both trees, read through git: each
Python file's imports (against its folder and what it puts on sys.path) and every path it names (a tracked file's path
or name as a literal, docstrings aside; an `os.path.join` of known parts naming a file or a folder), followed through
every Python file reached. A file in the closure is D; a root that loads code by a computed name, or reads files by
computed paths, escalates every other changed file to D? (D for its evidence, the lines that caused it said); code
outside is C; Markdown outside is A. It names what loosens a checker whatever the rung (a name dropped from
ADMISSION-0's expected checks, a detector or a budget made looser, a frozen reference rewritten, the vectors changed,
fewer plants), and what each rung needs. It never reads a commit message. `plants BASE HEAD` runs the suites' planted
defects in both trees (git worktrees) and fails if one the old checker refused passes the new, or is gone. Who runs
it: the copy the pushed tree holds, never the patch's (`git show origin/main:tools/rung.py > rung.py`, then `python
rung.py classify origin/main HEAD --repo .`); this first copy came with its own patch and was judged by nobody.
MEASURED in the container: RUNG SELFTEST 17/17 (a scratch tree: a helper imported through a folder put on sys.path, a
module loaded from a joined path, data named file by file and folder by folder, a file the change brings under an
import, a removed file of the checker, escalation by a computed import and by a computed read, the classifier and the
agents' rules changed, three loosenings and one addition that loosens nothing, the plants compared; and this
repository at HEAD: 309 files in the closure), 13 of 13 mutants of the classifier caught. On this series: 0220, 0221
and 0222 each classify D, every file in the closure or escalated — art/dress.py is the closure's through art/play.py,
the renderer through art/play.py and QUALITY-0, the providers through the queue, and art/README.md through art/studio.py,
which reads its section on the art file into every provider's prompt (a document that runs, found by the reading, not
by its name); the docs escalate, because the base reads files by computed paths in about 400 places and verify.py
imports modules by computed names (verify.py:259, 13102). So in this repository a patch is rung D, and what D needs is
his run on his machine and the plants: `plants b8b2fe0 39b3265` PLANTS HELD (25 planted defects refused before, 65 after,
none lost). Not claimed: that the closure is complete (a computed path is escalated, not followed), or that a loosening
of a kind it does not look for is seen.

**0220 to 0223 on his machine, and 0224: a refusal answered only after its request is read (2026-10-14).** His first
`git am` of 0221 failed on AGENTS.md, docs/CORE.md and docs/ROADMAP.md: his checkout was at 0219 (tree c140fe20), 0220
not yet applied, and 0221 edits lines 0220 adds (the same three files fail on 0219's tree here, and 0220 then 0221 to
0223 reach the predicted tree). Aborted, then applied in order: 0220 as tree db333247 and 0223 as tree 733ab149, both
as predicted. On his machine (Windows, Python 3.14): QUALITY SELFTEST 58/58; ART CHECKS PASSED, **each brief equal to
its frozen reference** — harbor-day 549d5d76035f and plaza-night 99001240ed5c, frozen in the container under Python
3.11 on Linux: the first mechanical comparison of the exporter's bytes between two machines, two of two equal
(MEASURED); DIRECTOR SELFTEST PASSED, with ADMISSION-0's rows; DIRECTOR CRASHTEST PASSED (15 cases); DIRECTOR RACETEST
PASSED (32 cases); then STUDIO SELFTEST stopped after 13 rows, `ConnectionAbortedError: [WinError 10053]`, on the row
that gives a still with a token that is not the studio's. The cause: the server refused the still at once and closed
the connection with the request's body unread; the system then resets the connection, and Windows drops the answer
the client had not yet read (Linux hands it over first: in the container a client read the 403 in 10 of 10 trials,
bodies of 60 kB and 3 MB, MEASURED, which is why this row passed here). **0224, built, off the gate.** `art/play.py`:
every refusal of a POST (403, 400, 404) reads the request's body first, up to its limit (64 KiB for JSON, 32 MiB for a
still), with a timeout, then answers and closes. A new row holds it where the container can: the headers sent alone,
no answer comes while the body is still to come, then the 403; the plant (no draining) answers before the body.
`art/studio.py`: a request's line is written to its record before the request reads as ended (it was written just
after): a reader that waits for the end and then reads the record found no line in 1 of 2 runs of the studio's
self-test here before the change (the Claude Code row, IndexError), and cannot now. MEASURED in the container: STUDIO
SELFTEST 74/74 in 4 of 4 runs after it; STUDIO-2 SELFTEST 19/19 in 15 of 16 runs, and 17/19 once, its failing rows not kept (OBSERVED; the cause
not known); LIVE SELFTEST 18/18, STUDIO APP SELFTEST 12/12, STUDIO-TXN SELFTEST PASSED. Not measured: the new row on
Windows, which is where the reset happens; his run of the rest of 0223's list is still to come.

**0224 on his machine, and 0225: RULES-2, movers, in the simulation and its twin (2026-10-14).** His run of 0224, on
Windows: STUDIO SELFTEST 74/74, the new row among them, so a refusal now reaches the client where the reset happens
(MEASURED there); STUDIO-2 SELFTEST 19/19; LIVE SELFTEST 18/18; STUDIO APP SELFTEST 13/13 (the row reading a live
job's process list runs on Windows only); RUNG SELFTEST 17/17, the classifier giving 0224 rung D; PLANTS HELD (25
refused before, 65 after); the gate 251 rows / 0 fail; pushed b3050b1..52670bd. That closes the three items of his
order of 2026-10-13 that came before RULES-2 (0221 to 0223, and 0224 their fix). With it came his document
*Verification Complete: The Foundation Is Solid*, whose first milestone for RULES-2 is one mover and one rider (the
platform empty, a player standing on it, the player jumping off mid-motion), and three checks before it: the rules'
version in the tick's hash, independent test vectors, and a disposition for overflow. Where it describes the
foundation as proven 32-bit fixed point, that is not this repository: the simulation is binary64 under RULES-1, and
what has been compared between two machines is the exporter's bytes (0221), not a tick. **0225, built, off the
gate.** [`graybox/RULES-2.md`](../graybox/RULES-2.md): rules 1 with movers — boxes on one axis whose coordinates are
multiples of `Q` = 1/256 m below 1,024 m, moving ping-pong by whole phase units, so none of a mover's arithmetic rounds
in any engine; the mover step a slot of the tick after the spawn and before the yaw, one code path (a world without
movers plays the same ticks); a rider (on the ground, feet exactly on the top, overlapping in plan) carried by the
exact displacement, or the mover stopped when the carried body would be blocked; a mover that would enter a player
stopped (policy `stop`); a box wholly above the head a ceiling; a parked mover a static box; and a world refused
(`RULES2-MOVER`) unless every mover is slow enough that no tick can pass it through a player (`speed·Q < 2·radius + t`
along x or z, `height + t` along y). Every rules-2 hash is FNV-1a 64 seeded with an identity: `VERDANDI-RULES 2`, then
every constant (gravity and the timestep among them), the input contract's version, the map and every mover, each
number as its bits; the identity's own hash is reported beside a run. `GrayboxSim.withRules(2)` in `sim.js` (the
default stays rules 1) and `tick_ref.py rules2`, both written from the document. His three checks, as built: the
version and every parameter in every tick's hash (the identity); independent answers ([`rules2_cases.json`](../graybox/web/rules2_cases.json),
eleven cases whose values were worked by hand from the document, with the working, each implementation held to them
and not to the other, then to each other); overflow refused where a world is made (the bounds above), so no integer of
the mover arithmetic is ever outside what a double holds exactly. His milestone is K2 (a rider carried out and back,
x 46.25 at tick 1, 50 at 16, 49.75 at 17, 46 at 32), K4 (a rider jumping off mid-motion keeps none of the motion, x
47.25 at ticks 5, 6 and 8) and W2 (3,000 ticks of the stress run from the platform's top). MEASURED in the container:
`tick_ref.py rules2` RULES 2 HELD BY PYTHON (every worked value; K11, no movers, 157 ticks the same bytes as rules 1's but for the empty list of movers;
W1 and W2, 6,000 and 3,000 ticks among a deck, a lift and a wall, no tick ending with the body inside a box) and its
five plants in the Python tick each caught by a worked case (no carry, a wrap past 2·len, no stop, no ceiling, no
tunnelling bound); node v22 and headless Chromium 141 (`trace.py run tactical --rules2`) each RULES 2 HELD BY PYTHON
AND THE ENGINE, every snapshot, hash and identity the same over 9,284 ticks; rules 1 unchanged: GRAYBOX SELFTEST 30/30
and 27/27, TICK REFERENCE VERIFIED, TICK-REF SELFTEST PASSED, RULES REFERENCE PASSED, INPUT CONTRACT HELD BY PYTHON AND
THE BROWSER. NOT_MEASURED: Firefox (none in the container), and his machine. No page plays rules 2 yet.

**A measurement for his open-world proposal (`graybox/translate_probe.py`).** His second document, *The Continuous
Open-World Coordinate Solution*, rests its determinism on moving the origin changing nothing. The probe plays rules 1's
stress run (3,600 ticks, from spawn A) on the tactical map and on the same map moved by 2^k m along x and z, k = 7, 10,
14, 17, 20 and 23 (a whole number of cells), and sets the two runs against each other tick by tick. MEASURED: at every
offset the runs part from tick 1; the widest gap grows from 5.65e-13 m (128 m) to 3.95e-08 m (8,388.61 km), where
doubles are 1.86e-09 m apart; in no run did a cell, the footing or a hit differ. So rules 1 are deterministic and not
translation-invariant bit for bit: a world rebased in the middle of a run plays different bits afterwards, which makes
a rebase a step of the rules, at a defined tick, done the same by both implementations, and not a change of view or an
admission. What it does not show: another map, a longer run (a gap can grow until a discrete outcome differs), rules 2,
or an engine other than Python's arithmetic. Next: 0226, the art language's mover statement (`art/dress.py`, which
moves every world's head once, with the number grammar's fix), QUALITY-0 and ADMISSION-0 learning movers, the scene
renderer drawing them, the plaza playing `withRules(2)` by the version handshake, and the exporter's checks of swept
boxes against rock, spawns and each other; his references frozen again after it.

**0225 on his machine, and 0226: movers enter through the art language (2026-10-14).** His run of 0225 (Windows,
Python 3.14, Edge 155): applied as tree d228b6dc, as predicted; `tick_ref.py rules2` RULES 2 HELD BY PYTHON, line for
line the container's; then, the browser's run made, RULES 2 HELD BY PYTHON AND THE ENGINE: every snapshot, hash and
**identity** the same over 9,284 ticks, the identities the container's (fa57af895f527fdf to dd2eeb4aa57b16d0) —
rules 2 agreeing across machines and engines (V8 in Edge on Windows, V8 in node and Chromium 141 on Linux, CPython 3.11
and 3.14), MEASURED; RULES REFERENCE PASSED; GRAYBOX SELFTEST 30/30 and 27/27; the translation probe's six lines as
the container printed them (to the three digits printed: not a comparison of bits); the gate 251 rows / 0 fail, rowset
74db4c8d78625af5; pushed 52670bd..cc8ed69. Not run there: rules 1's trace held to Python (`tick_ref.py verify`) and
Firefox. His first comparison was asked for before the browser had written its file, and `tick_ref.py` played the
whole table and then stopped on a traceback: it now says which file is missing and the command that writes it, before
playing anything. **0226, built, off the gate**, by his ruling that *"the physics layer should enter through the
existing exporter, extending `art/dress.py` so that motion and interaction statements become part of the art language
itself"*, the exporter change that moves every head once carrying the number grammar found in 0221. `art/dress.py`:
**the number grammar** — a number is ASCII digits, at most one `.` between digits, a `-` in front when negative;
`2_5`, `+2.5`, `25e-1`, `.5`, `5.` and digits of other scripts are refused (float() took them, MEASURED in 0221); a
spacing, a percentage or an `every` must be whole (`int()` cut `2.7` to 2 without a word); a colour's channels and a
cell's coordinates ASCII (`str.isdigit()` took a superscript two, which `int()` then refused with an error the exporter
did not catch: a crash, now a refusal). **The mover statement**, `mover NAME MATERIAL X0,Y0,Z0 X1,Y1,Z1 along AXIS
travel METRES speed M/S`: its corners and travel whole numbers of 1/256 m (exactly, through `Fraction`), its speed a
whole number of 1/256 m a tick (a refusal names the two nearest speeds); held to rules 2's own table by the twin's
`Mover` (the tunnelling bound among it), and its travel to the world: inside the grid, above every cell it crosses,
clear of every spawn's column, of every target's column (rules 2 do not move targets: a box would pass through one),
of every other mover's travel, and of every piece of dressing but what lies flat on the floor. The reach ceiling counts a rider at each mover's highest top (every mover taken to be boardable, which can
only raise it) and the cells a rider can step off onto. A scene with movers names `rules: 2` and carries them; a scene
without is byte for byte what it was (harbor-day 549d5d76035f and plaza-night 99001240ed5c, the same scenes and plan
views as before), so the only head that moves is the exporter's: recorded in the plaza's ledger by a rebase (#24,
1ff8e5e8f6be to aaf42446abed). `art/check.py` holds movers apart from the exporter's code: the handshake (a scene
names rules 2, which `sim.js` and `tick_ref.py` both say they implement, read from their sources, with the same unit
and the same body), rules 2's table restated, every travel against the world, the spawns, the targets and the other
movers, a rider in the reach ceiling, no dressing in a path; twenty-two new plants in every brief (the grammar's six
beside a lamp the exporter takes; eight movers the exporter refuses beside one it takes; a slab clear of every head on
foot refused once a lift stands under it; seven defects planted in the brief's scene with a lift, which itself passes
every check, among them rules 3, a travel through a target's column — and the same scene over a world without targets
passing, so that the refusal is the target's — and a rider left out of the ceiling). QUALITY-0 knows `rules` and `movers` (both or
neither, rules 2 only, every field bounded, every travel inside the world and under 1,024 m) and the renderer's mover cap
(64, read from its source). The scope protocol: a mover is play (`play/mover/NAME`), and any change to one, or to the
rules, is refused whatever is granted (SCOPE-PLAY), its material being its look (`surface/mover`); three new vectors
fix it (65 in all, the 62 before byte for byte the same), the Rust twin reproduces all 65, and each twin with the rule
taken out fails the vector it should. So a mover enters a world by a person's edit, recorded with `rebase`, never
through a prompt, and the studio still names `motion.path` among what it cannot make. ADMISSION-0: the movers' check
among the expected ones, `mover` among the play kinds, `sim.js` and `tick_ref.py` among the components a verdict rests
on, and a scene with movers says that no tick was run. The plaza: `play.js` plays a scene under the rules it names and
no other (rules 2 with its movers; a scene naming rules it does not play is not played), starts a new game when the
movers or the rules change and not when only their look does; `scene_render.js` draws each mover where the simulation
has put it (no moon shadow: that map is drawn once). The Unreal importer refuses a scene with movers. A world to play
them: `art/briefs/harbor-lift.art`, harbor-day with a deck sliding 16 m along the south lane at 3.75 m/s and a lift
beside the 2.6 m block at its west end, rising 2.25 m at 0.9375 m/s. MEASURED in the container: ART CHECKS all PASS
but the three references (the exporter changed; his act to freeze, the comparison saying no field moved for harbor-day
and plaza-night); QUALITY SELFTEST 73/73; DIRECTOR SELFTEST PASSED (a new row: an intent adding a lift refused,
SCOPE-PLAY, its record saying the mover was not played), CRASHTEST (15 cases) and RACETEST (32 cases) PASSED; VECTORS
65 / 65 and CONFORMANCE 65 / 65; LIVE SELFTEST 20/20 (a lift added to the art served under rules 2; a mover through a
wall refused, the scene before it served); STUDIO SELFTEST 74/74; STUDIO-2 SELFTEST 19/19; STUDIO APP SELFTEST 12/12;
STUDIO-TXN SELFTEST PASSED; RUNG SELFTEST 17/17; `tools/rung.py classify` D (the twins, AGENTS.md and the art's checks
are roots), and `plants` NOT HELD with one plant *gone*, read and kept so: QUALITY-0's *a field the checker does not know
(movers)* cannot stand now that movers are a known field, and is planted as *(doors)*, the same defect under another
name, beside thirteen plants of the movers' own fields — the comparison is right to stop on it, and a person to read
it. In headless Chromium (not committed), harbor-lift played: rules 2 and
its two movers; the movers moving; a rider carried 0.5 m by the deck in 16 ticks and 0.78125 m up by the lift in 100,
exactly; the lift to the block's top and a step east onto it; the movers taken out of the art on disk, a new game under
rules 1, and put back; a change of their material alone leaving the game untouched; no page error. OBSERVED there
(SwiftShader): the lift a dark steel slab beside the block, at its top level with it; the detectors flag neither still.
Not measured: his machine; a real GPU; a person riding it.

### DIRECTOR-0 — the operator loop: scope declared, verdicts head-specific, intent kept · **the owner's ruling** (2026-10-10); outside the certified gate · **built** (`art/director.py`, `art/director/`)

**His ruling.** *"The goal is now a prompt-driven art director with a trustworthy, editable change loop—not another
verification campaign."* He accepted the first-slice scope the research supported. It has five parts: a canonical
intent; a reference graph with early cutoff; a pure `check_scope` with shared conformance vectors; a structural diff;
and visual anchors as provenance only. Futures, playtesting, signing, replay certificates and memory are deferred. He
locked three boundaries:

- canonicalization *"must be a defined contract, not 'sorted JSON'"*;
- early cutoff *"must depend on content identity"*;
- *"A scope verdict must name the head it checked."*

**His five further boundaries, with the word "Go":**

1. The vectors are the new end-to-end path, *"consumable by a second implementation without importing or executing
   the Python reference implementation"*, comparing verdicts and canonical outputs, *"not just whether both
   implementations return PASS"*.
2. The protocol is pure and versioned, with no claim of RFC 8785 compatibility it does not have.
3. Scope decisions are head-specific, with no stale-verdict override.
4. The ledger is append-only in behaviour: a re-evaluation is a new event, and the old verdict is kept.
5. The plaza's candidates exercise the protocol, not only its happy path: a valid change of the look, a layout
   change, a stale candidate, an out-of-scope change that must be refused, and malformed or unknown-version input.

His last word on it: *"Then stop expanding protocol machinery and use it to make the plaza. The protocol exists to
protect the creator's intent—not to become the product."*

**Grade.** DECLARED: his ruling. It is not a rung, it adds no row, and the gate does not read `art/`.

**Built (2026-10-10).**

- **The canonical form** (VERDANDI-CANON 0, `art/director/intent.py`): a restricted JSON defined rule by rule. Values
  are strings, booleans, arrays and objects only, integers are strings, keys are ASCII, escapes are exact, output is
  ASCII only, and a document is admitted only in its own byte form. It says plainly that it is not RFC 8785.
- **The intent** (version 0): an unknown version is refused, never translated.
- **The scope protocol** (`art/director/scope.py`): one pure function. It works over stable addresses, a
  piece-to-material graph with early cutoff and a cycle check, patterns with namespaces granted only by name,
  `layout/` and `surface/` grants, and a play scope that can never be granted. Its verdicts are CLEAN, LEAKAGE or
  REFUSED, each naming the head written against and the head checked.
- **The ledger** (`art/director/ledger.py`): one canonical document a line, hash-chained. Its events are genesis,
  evaluate, refuse_input, admit, refuse, rebase and approve, and `verify` replays it to the files.
- **The conformance vectors** (`art/director/vectors.json`, 62): the canonical form, its refusals, intents, heads,
  material digests, patterns and fifteen scope cases, all with exact expected bytes.
  - The Python reference reproduces them, and so does a second implementation, `art/director/conform.rs`: std-only
    Rust with its own JSON reader, which never runs the Python.
  - Tampered expectations are caught by both.
  - Of four rule defects planted in the Rust copy, three were caught. The fourth (DEL left unescaped by one branch)
    was equivalent, since the next branch escapes it; planted as a real defect, it was caught.
- **The first round**, "make the plaza more imposing" (`art/rounds/plaza-imposing/`), evaluated in 3.5 s:
  - **A** (monumental towers): CLEAN.
  - **B** (a layout change closing the north flank to a slot, through the design tool): CLEAN.
  - **C** (heavier cantilevers): CLEAN.
  - **D** ("for the plaza", but through shared materials): LEAKAGE, reaching the bases' towers, every wall and the mid
    lanes' neon.
  - **E** (sealing the south flank under a plaza-only grant): REFUSED.
  - **F** (a slab at 3.6 m over the platform): REFUSED.
  - An unknown version and a malformed input were refused on input.
- **The self-test** (`python art/director.py selftest`) runs the lifecycle in a scratch copy:
  - it admits A;
  - it refuses to admit C at the moved head, re-evaluates C as a new event naming the old one, and admits it;
  - it refuses D on a person's word, then re-evaluates and admits B (whose layout is admitted through the design tool);
  - it verifies the ledger, refuses two planted defects (an unlogged hand edit, a changed ledger line), and accepts a
    hand edit recorded with rebase.
- **The one-place rule**, which a piece's identity rests on, is part of this slice. It found two puddles in one place
  in the first brief, and the brief's mid lane became two regions.
- **Choices are keyed by a statement's name, not its text**, so a revision of a statement's numbers no longer
  reshuffles its other choices.

**What it does not show.** That the art is good: no check here measures it. That either implementation is right: one
author wrote both, and the vectors are the contract. That the ledger's last line is protected: nothing after it names
it, so it rests on the commit that holds it.

**Next, by his ruling.** The owner chooses from the round (`python art/director.py admit plaza-night <seq>`, or in the
session). Then the plaza is made in Unreal.

**The round admitted (2026-10-10).** His choice: *"Choose A, B and C — admit all three, sequentially, through the
ledger."* A first, to *"establish the vertical silhouette"*; B, to *"reshape the approach"*; C last, to *"add overhead
framing after the first two changes have been re-evaluated against the current head"*. His condition was to inspect
the result after each admission before the next, and to stop and revise the art direction if a change made the
composition worse, *"rather than admitting changes just because their scope checks pass"*. In his words, *"CLEAN means
the candidate satisfies the scope rule; it does not mean the scene is artistically better."*

- **The ledger.** A was admitted at #9. B was re-evaluated at #10 (CLEAN, HEAD-MOVED) and admitted at #11, its layout
  through the design tool. C was re-evaluated at #12 (CLEAN, HEAD-MOVED) and admitted at #13. The head moved from
  `88c5151740aa` to `c53d87349709`. D, E and F stand evaluated, neither admitted nor refused.
- **The checks after each admission.** The ledger verified and `art/check.py` passed. After B, the graybox's map checks
  passed (the tactical layout compiled again through the design tool, head `1c80227de403`), and so did its runtime
  self-test (23 / 23). These were run here, in the build container.
- **The judgement, from the provisional preview's stills** (OBSERVED, in a software renderer; a sketch, not the
  Unreal look).
  - **After A**, from eye level the towers change little. From 30 m, the plaza's crown stands above the skyline. The
    towers, one prism per cell, read as a comb of spikes rather than one brutalist mass: a note for the kit, not a
    reason to stop.
  - **After B**, from the slot the plaza is framed in a narrow lit opening, the compression B intended. From the
    north-flank view the new wall fills half the frame, and a lamp over every cell washes it flat and pale: a note for
    the lighting.
  - **After C**, inside the plaza at eye level the slabs at 7 m mostly leave the frame. The west bridge reads as a
    lintel over the approaches from base A and the mid-west lane, so the plaza is entered as through a gate. Looking
    up, the sky is framed. The heavier slabs will need light on their undersides to read at night.

  No admission made the composition worse, so all three were admitted.
- **Two defects it found, both tests whose fixture was the live state.**
  - The director's self-test copied the live brief. Once A was admitted for real, A's `+ material` no longer applied,
    and the self-test failed. Its fixture is now the round's `base/`: the files at the head its candidates were
    written against. The self-test checks that its scratch copy starts at that head, and a planted change to the
    fixture is refused.
  - The art check's layout revision closed the same three cells of the north flank that B admitted. After B it had
    nothing to test and said SKIPPED. It now narrows the south flank, and it and its plant run again.

**Next.** The plaza is made in Unreal: brutalist massing in place of the per-cell prisms, wet concrete, controlled
neon, rain, fog and light. The certified layout and collision stay authoritative.

### ART-GENERATION-0 — prompted art over a playable world · **the owner's pivot** (2026-10-10); outside the certified gate · **built** (its first slice, `art/`); the Unreal import not yet run on an engine

**His words.** *"the verification should exist only to guarantee the purity of the art. we want to move from
verification to enabling the user to prompt art through llm and i mean at the quality of aaa games"*. With them came a
text he brought. It names the slice and its loop: intent, art direction, world, play, critique and revision. It keeps
a small set of guarantees (provenance from source to scene, geometry integrity, edit locality, reproducibility,
performance budgets, playability), each in proportion to the harm it prevents. It holds that visual quality is
judged from rendered views and by people, not certified by tests, and that the repository should be read before
choosing between extending the renderer, connecting an engine or a hybrid.

**The reading of the repository** (2026-10-10, in the session). The certified kernel is an integer raycaster over a
grid of at most 48 × 48 cells. No growth of it reaches the target, and it is the truth about layout. The design tool
and the graybox are already the stage studios call blockout: a layout a model can propose and the owner admits, a
collision world derived from it, routes walked and planted defects refused. So the path is hybrid. Verðandi keeps
layout, collision and lineage; an engine renders; the model directs the art in between.

**His decision, answering the session's three questions.** *"Finite decision: Unreal; curated modular assets + CC0 +
selective AI props; separate `graybox/` project. Keep verification subordinate to artistic intent and gameplay
integrity."* His qualification: *"prove the smallest end-to-end scene works on your actual hardware before committing
to its full toolchain"*, and Godot is the fallback if Unreal proves too heavy. His first milestone: *"one rain-soaked
brutalist coastal plaza at night that you can actually enter in first person, critique in plain language and revise.
Make one layout change and one visual change. Verify that collision and routes survive both, that unrelated regions
remain untouched, and that the scene loads. Judge visual quality from actual rendered viewpoints—not from a passing
gate."*

**Grade.** DECLARED: his ruling. It is not a rung and adds no row. It goes ahead of EVIDENCE-LINK-0, which stays
declared as written.

**Built (2026-10-10), beside the certified tree: `art/`** ([`art/README.md`](../art/README.md)). The project is named
`art/` because `graybox/` is the slice it dresses.

- **An art file** in its own small language (`VERDANDI-ART 0`). It sets materials, massing (skyline, towers),
  canopies, neon, lamps, puddles, air and critique views. Every mesh it uses names its source and licence.
- **An exporter**, `art/dress.py`. It turns the art file, plus the W and C of the graybox map it names, into one
  engine scene. The scene's collision is C exactly, merged inside 8 × 8 chunks. Every dressing choice is a hash of
  its statement and cell, so an edit cannot reshuffle the art elsewhere. A lineage binds the art file, the layout's
  heads, W, C, the exporter and the scene.
- **The art's checks**, `art/check.py`. They cover the export's determinism and the graybox map's own checks. The
  collision boxes must lay back onto C cell for cell. No dressing may stand where a player can be: every piece must
  be inside rock, inside or flat on a solid top, flush on a rock face, or above a reach ceiling recomputed from C and
  the player, whose constants are read from `graybox/web/sim.js` itself. No piece may have collision. Every mesh must have a source and licence, and the lineage must hold.
- **Eighteen planted defects**, each refused by the check that should catch it. Five are statements the exporter
  itself must refuse.
- **The two revisions of his milestone.** The look revision, "make the wet surfaces less reflective", changes the
  three materials it names and nothing else. The layout revision, "make this alley narrower", closes one column of
  the north flank through the design tool's own preview and admission. Play still holds after it: three cells
  changed, all in its region, and nine pieces of the scene changed, all beside them.
- **The Unreal 5.8 importer**, `art/unreal/verdandi_import.py`, run inside the editor. It works in one undoable
  transaction. It keeps every actor whose item did not change, checks the level's collision against C, reports the
  template character's movement against the player the checks assume, and writes a report beside the scene.

**What it does not show.** The importer has run only against a stand-in for Unreal's Python module, outside the
repository. Its first run on an engine is the host's, and its report is the evidence. The first scene uses the
engine's cube alone: it is the hardware test, not the look. There is no kit yet, no textures, no rain particles and
no AI props. Visual quality is NOT_MEASURED: no check measures it, and none is claimed.

**Next, by his milestone.** On the host:

1. Install Unreal 5.8.
2. Create a First Person project in `art/unreal/VerdandiArt`.
3. Import the scene, enter it, and critique it from the views.
4. Re-import after each revision.

Then the kit: a curated modular set, CC0 materials and selected AI props, each declared with its source and licence
and placed under the same rule.

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

### Beyond the rung — eight ideas on composition, history, debt, attestation, hashing, compression, zero knowledge and proof strength · **ruled** (a text the owner brought, and his rulings on it, 2026-10-09); nothing built

**The text.** It asks what happens when proofs are composed — whether ⊢R1 and ⊢R2 give ⊢R1∘R2, so that one theorem
could certify the whole ladder — and offers seven more ideas: amendment chains that fork and merge; proof debt as a
weighted score with a budget; hardware-signed witness chains; semantic hashes beside byte hashes; a Merkle tree over
row results; zero-knowledge proofs that a row ran; proof strength scaled by a row's criticality and age. It
recommends starting with proof debt and semantic hashing.

**His rulings.**

| the idea | his ruling | his reason, close to his words |
|---|---|---|
| proof composition | accept the question, reject the shortcut; DEFER as a rung | ⊢R1 ∧ ⊢R2 ⇒ ⊢(R1∘R2) is not valid without conditions: interfaces, assumptions, environments and evidence identities have to line up. A matching reconstruction in a second container establishes neither independence of the environment nor of the checkers. First, certificates with stable interfaces, explicit assumptions and exported obligations; EVIDENCE-LINK-0 is a sensible prerequisite |
| branching amendment chains | accept the model (a DAG, not a tree), DEFER | a merge names both parents and the decision; two branches that pass do not make a merge that passes, which is a new artifact. No defect in the linear chain demands it |
| proof debt | ACCEPT a qualitative proof-obligation ledger as a practice; defer any score | multiplying severity, likelihood and cost invents precision; a budget may bound accepted residual risk and must never make an unproved critical invariant acceptable by its total. G29, G31 and G33 are not interchangeable debts |
| hardware-signed witnesses | DEFER | an attestation binds which process claims to have made an artifact; it does not show the compiler correct, the machine uncompromised, the tests sufficient or the output free of hidden dependencies. First, witness records bound to recomputable source evidence |
| semantic hashing | ACCEPT two identities, defer the build | H_byte identifies the artifact; H_sem identifies its canonical form under a stated equivalence and inherits the canonicalizer's soundness. Only when a consumer needs semantic equality; never added because it is easy |
| proof compression | DEFER | a Merkle root shows a leaf belongs to a committed set; not that the row ran, that its verdict is true or that the set is complete. No storage or cost problem at this scale |
| zero-knowledge execution | REJECT for now; a research direction if confidentiality is ever required | a proof that a circuit's constraints hold is not a proof that the circuit is the gate or that its inputs came from the registered tree |
| adaptive proof strength | ACCEPT prioritization; defer automation | criticality sets where extra adversarial evidence goes, never a weaker baseline for a registered requirement; a row's age is a record of repeated behaviour, not of correctness |

**His conditions for composition**, should it come: the downstream assumptions are discharged by upstream guarantees
or kept as assumptions; the artifacts' identities and interfaces match exactly; the evidence is bound to the
registered source and its execution context; an independence claim has perturbation evidence and is not inferred
from a matching reconstruction; and the composed certificate keeps every unresolved obligation. The rule he writes
under them — C₁ ⊨ G₁ and C₂ ⊨ (G₁ ⇒ G₂) give C₁∘C₂ ⊨ G₂ — he marks as schematic and not a theorem of this gate.
Sequential validation, compositional verification, proof compression and environmental independence are four
obligations; composition can save repeated work after evidence exists, and cannot make evidence.

**His order.** HERMENEUTICS-0 through HERMENEUTICS-0a; EVIDENCE-LINK-0, narrow, external and read-only; a qualitative
proof-obligation ledger; semantic hashing registered only for a concrete comparison, byte identity kept regardless;
certificate composition after the evidence interfaces are explicit; branching history, Merkle packaging, hardware
attestation, adaptive campaigns and zero knowledge left until a real use justifies them. In his words: *a passing
result cannot inherit a guarantee that its inputs never established.*

**Grade.** DECLARED: the text and his rulings. Nothing was computed for this section.

### Toward the final gate — a PASS that means one precise thing · **declared** (a text the owner brought, 2026-10-09); his final ruling kept; nothing built

**The text.** Move from proving checks to proving the relations between checks, their inputs, their evidence and
the verdict. Six bridges between fields: relational databases and provenance; causal intervention and metamorphic
testing; assume–guarantee contracts; mutation testing as falsification; build provenance and event sourcing;
information flow. A certificate is sketched as a constrained join of six relations — registered claims, sources,
executions, verdicts, evidence and documentation claims — with anti-joins for claims nothing supports and two-sided
set equality for change closure; a row's verdict should not move when an input it does not declare is changed; and
a candidate name, RELATIONAL-CERT-0, is offered and not registered. Its pivots in order: EVIDENCE-LINK-0; a reach map
for registrations, computed before an entry is committed; dependency-directed environmental independence;
composable certificates. And a final PowerShell run in five phases: freeze the candidate's identity; run the
existing checks without changing what they mean; bind the evidence to the candidate; enforce the registered laws;
emit a certificate, not a green line. *I would not write a replacement gate command from memory.*

**His final ruling.**

| | |
|---|---|
| next registered work | HERMENEUTICS-0 through HERMENEUTICS-0a |
| next verification pivot | EVIDENCE-LINK-0 |
| next research theorem candidate | dependency-directed environmental independence |
| longer term | relational certificates with assume–guarantee composition |
| the final operational goal | a PowerShell run that proves the registered predicate from retained, independently checkable evidence — not a script that prints PASS |

*Every final claim must be traceable to its authority, every comparison must state what relation it checks, and
every guarantee must stop at the boundary of the evidence that supports it.*

**Set against the tree.** The witness already keeps PowerShell out of the evidence: it launches Git and the gate from
Python with raw bytes, reads the status, the tree id and the commit at three moments, runs the gate twice and the
design checks once as a separate condition, and holds FULL×2 as registered — stdout only — with stderr and the
commit recorded beside it and not in the predicate, as the text asks. Its warning on `$LASTEXITCODE` is right by
Microsoft's documentation: a native program's nonzero exit sets it and does not stop a script. Several of the operators it names have counterparts in rows that exist:
the two-sided layout relation in `designir-fence`, entries at their hashes, the watches' heard-against-registered
counts. The documentation relation is the one with none, which is EVIDENCE-LINK-0. Of its sources, two are cited for
claims they do not make: arXiv 2202.10766 is *Revisiting Semiring Provenance for Datalog* (Bourgaux, Bourhis,
Peterfreund and Thomazo, KR 2022), not a study of explanations; the Wiley STVR paper is Schuler and Zeller's
*Covering and Uncovering Equivalent Mutants* (2013), on equivalent mutants and not on subsumption.

**Grade.** DECLARED: the text and his ruling. The sources were looked up; nothing was built or run for this section.

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

Everything above obeys the same discipline that carried the render campaign. *(These are the certified tree's
invariants. By the owner's rulings of 2026-10-09 the graybox runtime stands beside that tree with its own checks —
its floats, its WebGL renderers and its maps are not held by them — and the full gate runs at release checkpoints.)*

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
