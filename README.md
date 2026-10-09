<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Verðandi — a windowed design workshop over a frozen oracle

`Verðandi` (Verdandi in ASCII, for the repository and the crate names) is the second norn: what is becoming,
beside `Urðr`, what has become. It is a deterministic 1080p game-rendering studio with a measurable
low-latency presentation path — the target stated as what can be measured, never as a claim. Its native
kernel reproduces the pixels of the certified renderer in [`Dedoc-9/Urdr`](https://github.com/Dedoc-9/Urdr)
bit for bit; its workshop turns an authored edit into a new authority and an exact consequence record; its
shell owns the window, the input and the presentation. Since the live rungs the shell also carries the session
being authored: one append-only log whose replay is the world on the screen, journaled as it grows, saved on
Esc, and verified by the workshop.

**Author:** Daniel J. Dillberg · **Contact:** [bigdilly95@gmail.com](mailto:bigdilly95@gmail.com)
**License:** [AGPL-3.0-only](LICENSE)

## The charter (ratified before the first commit)

    KERNEL
      deterministic · std-only · no shell dependency · no UI toolkit · no presentation API

    WORKSHOP
      owns authored edits · validates before projection · can create new authority
      records consequences · does not become renderer state accidentally

    SHELL
      owns window / input / presentation · contains no kernel logic
      contains no authority mirror · is replaceable

    UI
      viewport + HUD = the kernel's framebuffer, digest-pinned
      editor / inspector / tool panes = shell chrome, declared off-gate

    ORACLE
      Urðr is frozen evidence (the tags urdr-oracle-1 and urdr-oracle-2) · not a runtime dependency

The dependency rule, and its negation:

    oracle ──► kernel                    never:   kernel ──► shell
                 ▲                                kernel ──► workshop
                 │                                shell  ──► canonical authority
    workshop ────┘

    shell ──────► kernel framebuffer

A declared goal beside the charter (the owner's, 2026-10-02; the ratified block above is not edited, and nothing of
this is built): **Verðandi does not execute what the model writes; it records what the verifier admits.** A language
model may one day propose typed, anchored changes against the sealed session, from outside canonical authority; only
the verifier admits them, and the reference kernel shows their consequence. It is LLM-BUILDER-0 in
[`docs/ROADMAP.md`](docs/ROADMAP.md).

Declared with it (the owner's, 2026-10-03, and by his ruling what the studio builds towards; also beside the
charter, also unbuilt): **the engineering gate certifies
the program; a content admission layer certifies that an artifact conforms to the already-certified program; content
generation does not invoke the engineering gate.** A model may generate content freely and may not redefine the laws
content runs under. Language can propose, the verifier admits, the session records, the kernel renders. Whether this
becomes part of the ratified charter is the owner's to rule. The first rung towards it is built, and the first
admission is sealed on the host: ADMIT-0, the admission seam. In the owner's words, **the gate certifies the machine; ADMIT admits the
world's changes.**

The first tool on that seam is built, off the gate: [`design/`](design/README.md). A person, a script or a model
writes a few lines of design text; the tool compiles them, shows the current world against the proposed one, and,
on acceptance, gives the proposal to the shell to admit. No gate runs in that loop. By the owner's adjustment of
2026-10-06 the engineering seam is frozen, and a new gate is added only for a new engineering invariant.

Running that tool found one. A design of 60 operations was 60 runs of the shell, each verifying the whole session.
DESIGN-EVENT-0 is built for it: a design enters a session as one batch, refused whole or admitted by one
admission, and equal to the same operations admitted one at a time. A preview is that admission stopped before
anything is written.

## Why this repository exists (the measurement that preceded it)

Urðr grew to 1,612 files and a thirty-six-minute gate; the game/render kernel is one fortieth of that tree.
STUDIO-0 asked, before any second repository, whether a native kernel of the certified tile path could hit a
1080p frame budget on the owner's hardware: the placement (`tools/terrain/mantle_rs/mantle.rs`, std-only
Rust, vista + mantle in reduced rationals) reproduced all twenty witnesses on its first compile, and on the
owner's host it rendered the identity picture at p50 11,361 / p95 11,959 / p99 12,319 / max 12,388 µs —
within the 60 Hz budget of 16,667 µs unoptimised, over 144 and 240 Hz. Renderer time, not input-to-photon.
The decision rule fired: the studio's first row already existed. The old studio arc (`Ursprung/weltwerk`)
was measured too, and what it settled is recorded in the shell's contract: a shell that mirrors kernel logic
is a second authority.

## The blueprint

*The design on one page: the problem, what is and is not a goal, how the parts fit, and for each invariant the
mechanism that holds it and the row that goes red when it fails. The long form is
[`docs/PROGRAM.md`](docs/PROGRAM.md).*

**The problem.** A picture certified in one repository has to become a place where a world is authored while it is
shown, without the picture or the history ever resting on trust. Three things make that hard. A faster renderer is a
different program from the certified one. A live window has state a file does not have: keys, a mouse, a clock,
focus, a compositor. And whatever proposes a change (a hand today, a model one day) is outside the authority and has
to stay there.

**Goals.**

| # | Goal | How it is held |
|---|---|---|
| 1 | The same picture | The kernel reproduces the oracle's witnesses bit for bit. Every faster path is a sibling held byte for byte to a frozen reference that is never edited for speed. |
| 2 | One history | Every accepted change (a step, a look, an opened cell, a painted class, an admitted proposal) is one typed event in one append-only log. The world on the screen is that log's replay. |
| 3 | A history that outlives the run | An event is journaled before it counts. A session is saved, read back and verified before it counts as saved, and it replays to the same head on another machine. |
| 4 | Proposals admitted, never executed | A proposal is bytes in a line language with one recognizer. It is refused with a typed reason or it becomes one ordinary event. |
| 5 | Claims that carry their limits | Every record states its grade, what it certifies and what it must not be read as. A method is hash-locked before its number. |

**Not goals.** A general game engine. A latency, frame-rate or feel claim: timing is measured off the gate, on a
named host, in separate segments, and input to photon is not claimed. Running what a proposer writes. A signature: a
session's seal is a hash. A second platform's window.

**The parts.** Two times, kept apart: the gate certifies the program, and admission changes the world without
running the gate.

```text
  PROGRAM TIME    verify/verify.py: 251 rows, two passes byte-identical, or nothing landed

      oracle/   Urðr, frozen at two tags
         │      witnesses · corpus · the heading vocabulary
         ▼
      kernel/   the frozen references ──► their fast siblings, byte for byte
         ▲                                     │ framebuffer
         │ calls                               ▼
      workshop/  edit · session ·           shell/  window · input · tick · present · readback
                 sessionwalk verify ◄────────────── the live session · journal · seal · admit
                                  the saved file

  CONTENT TIME    a change to the world is admitted; the gate is not run for it

      key · mouse · script · proposal (VRDNP1) · batch (VRDNP2) ◄── design/  inspect · propose · preview · admit · undo
         │      bound, or recognized, to a typed action
         ▼
      one append-only log ──────────────► journal.vsj   a record is flushed before it counts
         │      replay: W, M, the camera, the head
         ▼
      kernel render ──► composite ──► SetDIBitsToDevice ──► the composed screen, read back
         │      Esc
         ▼
      session.json   sealed; verified before it counts ──► sessionwalk verify · the sealer · a record

  PLAY TIME       graybox/: a playable slice beside the certified tree; the gate is not run for it

      a layout the design tool admitted · a pinned level ──► level.py ──► W canonical ──► C collision
                                                                            │                │
                                                         render.js draws W ◄┘   sim.js moves against C ◄── WASD · mouse · fire
                                                         (lit and dressed; it decides nothing that blocks)
```

**The invariants.** Each is a property a part owes, the mechanism that holds it, and a row that goes red.

| Invariant | Mechanism | Row |
|---|---|---|
| The kernel's pixels are the oracle's | both witnesses recomputed against the tags on every gate | `kernel-oracle`, `kernel-corpus`, `bearing-oracle` |
| A fast path never moves a pixel | byte-identity to the frozen reference at every tread, partition and thread count | `gauntlet2-threaded-equiv`, `bearingfast-court` |
| A read cannot edit the authority | the borrow checker: the planted edit does not compile | `membrane-wall` |
| The bytes handed to the screen are the kernel's | the blit-hash law; the composed screen read back | `shell-blit-law`, `presentexact-court` |
| Order is meaning, batching is not | one fold over the log; a checkpoint and a full replay reach one head | `sessionwalk-interleave`, `sessionwalk-batch-invariance` |
| A live session is a file the workshop verifies | save, read back, replay, and only then count it saved | `livesession-save`, `livesession-recover` |
| A tick is recorded and is never authority | the same commands at other ticks save the same events and head | `simtick-equivalence` |
| A frame at a free heading is the reference's | every such frame recomputed before the save, one in 64 during the run | `simtick-certify`, `mouselook-sample` |
| A proposal has one reading | one recognizer, held against an independent one over every single-byte mutant of three proposals | `admit-reader`, `admit-single` |
| A stale proposal is refused, never rebased | its parent head must be the session's | `admit-anchor` |
| What is read back is one language | one Rust reader shared by path and an independent Python one give the same code and byte offset, or the same typed value; every writer checks its bytes first | `readercourt-agree`, `readercourt-corpus`, `readercourt-writers` |
| No verdict is stored as data | one firewall, written in two languages | `records-firewall`, `records-twins` |
| The method precedes the number | hash-locked entries, each with a failure condition | `records-preregistered` |

What these rows do not reach is in [`docs/GHOSTS.md`](docs/GHOSTS.md), and it is part of the design.

## What each folder holds

Each folder's README is its own blueprint: the contract, the parts, the invariants, dev notes, ghosts.

| Folder | Contract |
|---|---|
| [`oracle/`](oracle/README.md) | frozen evidence from Urðr at `urdr-oracle-1`: the contract record, the corpus inputs the kernel is compared against, and (`oracle/game/`, GAME-0) Urðr's game layer with its own suites; and at `urdr-oracle-2` (BEARING-0) the bearing camera's record and its registered table of headings. Read-only by convention; a change here is a new oracle, named. |
| [`kernel/`](kernel/README.md) | the deterministic per-frame work: a scene in, an index frame and a picture out, two witnesses. std-only. Since BEARING-0 also the reference bearing kernel (any registered heading), and since BEARING-FAST-0 its fast sibling, which the live editor renders through at a free heading (MOUSE-LOOK-0). |
| [`workshop/`](workshop/README.md) | the design loop: an edit in, a new authority out, a consequence record beside it. Validates before it projects. Its `sessionwalk verify` is the replay every saved live session is held to. |
| [`shell/`](shell/README.md) | the window: present the kernel's framebuffer, pump input, read the composed screen back. Since the live rungs also the loop, the tick, the live session's log with its journal and seal, and the admission seam. It renders nothing itself. |
| [`verify/`](verify/README.md) | the gate: every claim above as a row that can redden; two runs byte-identical or nothing landed. Beside it the registry of methods and the off-gate sealers. |

## The sequence, as built

Each rung stands on one already measurable. The ledger, [`verify/RUNGS.md`](verify/RUNGS.md), has every rung's
rows, grade, limits and falsifier; this is the order and the state.

    FOUNDATION      the charter (c3cda5a) · KERNEL-0 the placement reproduces the oracle · WORKSHOP-0/0b an
         │          edit is a new authority, three witness grains · HUD-0 the overlay is a frame · RECORD-0
         │          the envelope, the firewall, preregistration · SHELL-0/0a the blit-hash law, a real window ·
         │          MEMBRANE-0 the one-way law as a compile error · TEXT-0 the level as text
         │
    AUTHORING       WORKSHOP-1 the log is the history, undo is replay · INPUT-0 a walk replays headless ·
         │          SESSION-WALK moving and editing in one sealed chain · SHELL-PLAYBACK the window shows
         │          exactly that chain
         │
    RENDER SPEED    GAUNTLET-0 measure first (emit 695‰) · 1a/1b/1c the divide collapsed, then per row ·
         │          RE-BREAKDOWN-1 re-measure · LOCALITY-0 the blocked floor layout, locked · GAUNTLET-2
         │          partition invariance, then threads: T=8 locked, about 3.3× the baseline, every tread
         │          byte-identical
         │
    PRESENT PATH    LATENCY-0/1/1a/1R does the speed reach the glass (only out of phase) · FRAME-SPLIT-0 no
         │          single dominant phase · PRESENT-SCALE-0, PRESENT-STRETCH-0, ALLOC-REUSE-0/1 diagnostics
         │          and one adoption · PRESENTATION-CHOICE-0 the certified picture 1:1 · PRESENT-EXACT-0 the
         │          composed screen read back exact, locked · HOST-STATE-0/1, REFUSAL-LOG-0, RUN-LEDGER-0,
         │          REFUSAL-WHY-0/1 what a run leaves behind · DRIFT-0 sitting 1 of 3
         │
    EVIDENCE        GAME-0 Urðr's game layer carried, its 411 tests passing in place · ORACLE-D0 the third
         │          hash recomputed by Urðr's own code
         │
    THE LIVE LOOP   LIVE-LOOP-0 every composition rendered live · LIVE-INPUT-0 a key press is a session
         │          event · LIVE-SESSION-0 the session saved, resumed, recovered · LIVE-AUTHOR-0 the thing
         │          authored is what the next frame renders · HOLD-WALK-0 held keys walk the grid
         │                                                            each measured on the owner's host
         │
    THE TURN        BEARING-0 the bearing camera of urdr-oracle-2 carried, its reference placed ·
         │          BEARING-FAST-0 made fast, byte for byte (worst-camera p99 3,716 µs on the host; the
         │          sweep 622,440 of 622,440 equal) · SIM-TICK-0/0a the mouse-look rules as integer law,
         │          windowless · MOUSE-LOOK-0/0a a real mouse on those rules: on the host, 13,931 raw
         │          reports, 1,761 looks, every free-heading frame the reference's
         │
    ADMISSION       ADMIT-0 a proposal in VRDNP1 recognized or refused, admitted as one ordinary edit; the
         │          first admission sealed on the host, its head computed beforehand · READER-COURT-0 the
         │          saved form as one bounded language: one Rust reader, an independent Python reader, the
         │          same code and byte offset from both on 163,072 mutants; built, and on the host 226 of
         │          226 rows (the first run read 225; the one red was found by the new watch and fixed)
         │
    REFUSALS        REASON-COURT-0 every refusal the gate requires held to a registered reason: 145 refusal
         │          checks censused, 103 with a code and 42 a registered REFUSE(any); a watch over every child
         │          that does not end 0, reading only the code head; the sealers under one mutation and its
         │          closure (337ab021; built, six rows, 232 in the gate; on the host 232 of 232, pushed)
         │          · MINT-WATCH-0 every refusal raised inside the gate's own process claimed by row,
         │          class, site and count: 164 raise sites read from source, 142,082 mints measured in four
         │          configurations, heard by the interpreter's own raise event (cd1472ec; built, four rows,
         │          236 in the gate; on the host 236 of 236)
         │
    CONTENT TIME    design/ the design surface, off the gate: design text handed to the shell's compiler,
         │          its one batch previewed by the shell's dry run and admitted by the certified shell; driven
         │          alike by a person, a script or a model (built; a client of the compiler since
         │          DESIGN-IR/DIFF-0; its own seventeen checks; run on the host over ADMIT-0)
         │
    THE BATCH       DESIGN-EVENT-0 a canonical batch of 1 to 4,096 operations refused whole or admitted by
         │          one admission as that many ordinary edits, equal to the same operations one at a time;
         │          VRDNP2, a net change set with one byte form; a dry run bound to its admission; replay
         │          with an exact memo, the workshop with none (ae7cbb36; built, six rows, 242 in the gate;
         │          60 operations admitted one at a time before the seam existed reach the same head as
         │          one batch; on the host 242 of 242 on every run and FULL×2; pushed)
         │
    THE COMPILER    DESIGN-IR/DIFF-0 the design text is the source language, and its compile to the canonical
         │          VRDNP2 change set against a parent world is one tree-owned function: in the certified
         │          shell, apart from the admission, held against an independent reference and against the
         │          statements applied by the gate itself; the proposal id is the SHA-256 of the design's
         │          exact bytes (2baa42f3; its round named before the build, c414587d; built, five rows,
         │          247 in the gate: the registered design compiles to its registered bytes and reaches its
         │          registered world; eleven planted compilers caught; on the host 247 of 247 twice on one
         │          tree, FULL×2; pushed)
         │
    A REPAIR        INPUT-0a a walk's path is the rest of its line: G31, a checkout path with a space, found
         │          by a perturbed pass and measured on the host, repaired before the next rung (2f0426d6;
         │          built, 247 rows; the pass that found it, run again as predicted, 247 / 0; on the host the
         │          clone with a space, 247 / 0 twice, FULL×2; pushed)
         │          INPUT-0b the walk's rows ask for the kernel and the walk program where they use them, and
         │          pass run alone (a167c308; built, 247 rows; FULL×2 on the host by the witness; pushed;
         │          closed)
         │
    THE MEANING     HERMENEUTICS-0 what the design language means, apart from the two programs that compile
         │          it: one reading ratified by the owner (a statement is a constant write, a design is its
         │          statements later-wins), six cases locked, four laws as theorems, ten designs with literal
         │          targets typed by hand (22d52d02; built under the owner's amendment 7e012752, four rows,
         │          251 in the gate: both programs reach every literal and keep the four laws; five
         │          misreadings planted alike in both, each caught; FULL×2 on the host; pushed; frozen)
         │
    THE GAME        FPS-GRAYBOX-0 the playable slice, by the owner's sprint ruling (2026-10-09): the gate stops
         │          growing; a first-person graybox on the canonical level — walls and floor admitted through
         │          the design tool, height, cover and play in an overlay beside them — walked, jumped and shot
         │          in the browser: `python graybox/serve.py` (built; not a rung; on the host the map checks and
         │          both self-tests pass; a mouse that was not captured was repaired, and the owner has played it)
         │
    THE LOOK        FPS-VISUAL-0, by the owner's ruling (2026-10-09), outside the gate: a sky and a traced sun,
         │          floor modules, panelled walls and dressed cover, a weapon model apart from the shot; the first
         │          renderer kept beside it (`--renderer flat`); the drawn solids held to the collision world face
         │          by face, decoration kept out of play (built; on the host's GPU the lit renderer 1.4 to 1.5
         │          times the first, under 2 ms a draw and readback at 1280 × 720; pushed, 3dc15ec..222f856)
         ⋮
    declared        EVIDENCE-LINK-0, each copied claim about a recorded event traced to its source (accepted as
                    the next slice); LIVE-AI-EDIT-0 → GUI (the owner's order; none registered); semiotics, a
                    vocabulary audit; design objects and constraints, each a court of its own; a competitive
                    arena, whose claims would be executable constraints and not a proof of fairness;
                    environmental independence, accepted as an audit and deferred; PERSPECTIVE-0, observation
                    stratified from action and claim; REFLEX, nine steps toward a certificate of who may observe
                    and who may change; the presentation and latency measurement; PRESENT-1; a design language
                    with many editors

The order first ratified named a strip cache as GAUNTLET-0 and ended in MATERIAL-0, a picture becoming a material
under a gate. GAUNTLET-0 became a measurement instead, and MATERIAL-0 is not seated.

`D_0`, the third hash in the oracle, is Urðr's composed CORE identity (level, entity, RNG stream, action log)
and is evidence, not the studio's: it is recomputed at gate time by Urðr's own `statecanon`, in place in the
carried game layer (row `oracle-d0`), and the studio still does not mint it. New VIEW semantics the
studio did not inherit (filtering, variety) may be earned by either route — in Urðr and re-frozen here as a
new oracle, or by a Verðandi-local reference pinned by rows here, as the HUD's pins are; CORE semantics have
one route only. Which, is decided when such a rung is seated.

## Running

    python verify/verify.py                                  # the gate; needs rustc for the kernel rows
    rustc -O kernel/main.rs -o verify/build/kernel           # the kernel alone
    verify/build/kernel --level oracle/levels/witness.lvl --tiles oracle/tiles/identity.tiles --camera 34,28,W
    verify/build/kernel ... --bench 200 --warm 20            # off-gate: renderer time on this host
    verify/build/kernel ... --hud --write-png out.ppm         # the composite with the overlay, to look at
    verify/build/kernel --level oracle/levels/witness.lvl --tiles oracle/tiles/identity.tiles --at 34,28,123457 --write-png turned.ppm   # BEARING-0: the reference at a heading id
    python verify/bearingfast.py --host $env:COMPUTERNAME     # off-gate: BEARING-FAST-0's speed court, sealed
    verify/build/shell simtick-selftest --script "0:m+3,15625:W,31250:PGUP,46875:m-2,62500:ESC"   # SIM-TICK-0: a windowless tick run (T:m+N a mouse report at T microseconds, T:KEY, T:KEY+ an auto-repeat, PGUP/PGDN/TAB the sensitivity keys), saved under build/sessions/
    verify/build/shell simtick-law                             # SIM-TICK-0: the laws as lines (the tick, the nearest cardinal of every id, the delta)
    verify/build/shell look-selftest --script "0:m+3,20000:W,40000:blur,60000:m+9,80000:focus,100000:m-2,300000:ESC"   # MOUSE-LOOK-0: the live loop under a tick source, on the mock (a scripted mouse, keyboard and focus; the clock is the composition count), saved under build/sessions/
    verify/build/shell admit-anchor --session build/sessions/<run_id>/session.json   # ADMIT-0: the four lines a proposal for that saved session begins with (VRDNP1, renderer=, bearing=, parent=); reads only
    verify/build/shell admit --session build/sessions/<run_id>/session.json --proposal p.vrdnp --allow open,close --cells 1,1,62,62   # ADMIT-0: the proposal (eight lines of VRDNP1) recognized or refused with a typed reason; admitted, it is one edit in a new saved session with its envelope beside it; the grant is this command line's
    python verify/bearingsweep.py --host $env:COMPUTERNAME    # off-gate: BEARING-FAST-0's sweep (about an hour), sealed
    python verify/bench.py --host $env:COMPUTERNAME           # off-gate: the kernel's frame time, sealed under the envelope
    verify/build/shell witness --level oracle/levels/witness.lvl --tiles oracle/tiles/identity.tiles --camera 34,28,W
    rustc -O --cfg shell_window shell/main.rs -o verify/build/shell.exe   # Windows: build WITH the window
    verify/build/shell.exe run --level ... --camera 34,28,W --measure 200 --host $env:COMPUTERNAME   # the window + present timing
    verify/build/shell.exe show --level ... --camera 34,28,W                    # the certified picture 1:1, the screen read back; Esc closes
    verify/build/shell.exe show-playback --session workshop/attest/sessionwalk-demo.json   # a sealed session, 1:1, each frame read back
    verify/build/shell.exe look-window                          # MOUSE-LOOK-0: the live editor with the mouse — move it to turn, W/S walk, A/D strafe, PgUp/PgDn/Tab the sensitivity; captured while the window is in the foreground; Esc ends and saves
    verify/build/shell.exe live-window                          # LIVE-AUTHOR-0: the live editor on keys alone — walk, Space opens or closes the faced cell, 1-5 paint a tile class; Esc ends and saves under build/sessions/
    verify/build/shell.exe live-window --resume build/sessions/<run_id>/session.json   # LIVE-SESSION-0: continue a saved session (or a crashed run's journal.vsj) into a new file; the parent is never modified
    rustc -O workshop/sessionwalk.rs -o verify/build/sessionwalk   # the workshop's session-walk tool
    verify/build/sessionwalk verify --session build/sessions/<run_id>/session.json    # the workshop's own replay of a saved session: every witness and the head
    python verify/livesession.py --host $env:COMPUTERNAME --session build/sessions/<run_id>/session.json   # off-gate: seal a saved session as a record under shell/attest/
    rustc -O workshop/edit.rs -o verify/build/edit           # the workshop
    verify/build/edit record --level oracle/levels/witness.lvl --tiles oracle/tiles/identity.tiles \
        --camera 34,28,W --edit cell:31,27,. --out-dir out --name cell
    verify/build/edit check --record out/cell.record.json

Landing condition: two consecutive gate runs byte-identical and `GATE PASSED`. The ledger is
[`verify/RUNGS.md`](verify/RUNGS.md).

## Discipline

Every claim is graded — MEASURED, ESTABLISHED, DECLARED — with a `does_not_show` boundary and a falsifier that
can fail. Tests assert the apparatus (the plant bites), never a hoped outcome. Two witnesses per row where
two quantities exist (geometry and appearance), never one. Wall-clock is off-gate, on a named host, with the
witnesses checked before any number is printed. `integrity ≠ truth`; `built ≠ adopted`; `declared ≠ verified`.

The performance courts isolate their measurements under a formal boundary condition,
[`EPISTEMIC-INVARIANCE.md`](EPISTEMIC-INVARIANCE.md) — the author's *Epistemic Invariance of the Boundary* theorem,
which dictates that a layout mutation's cost is extractable only when the execution boundary is held
microarchitecturally static (monomorphize, process-isolate, interleave), and which honestly bounds what its own
formalism proves. First applied by `LOCALITY-0`, whose court fired **Exit 1** (blocked wins): the 8×8 cache-blocked
floor layout, byte-identical and faster, was `LOCK`ed as the accepted single-thread `emit` and sealed as GAUNTLET-2's
hard baseline, with the linear-fetch DDA retained verbatim as an immutable reference witness.

## Dev notes

Short forms of what the work taught. The long forms are in [`docs/DEVNOTES.md`](docs/DEVNOTES.md).

- **Measure, then choose.** The most useful rungs committed no optimization: GAUNTLET-0 named the target,
  RE-BREAKDOWN-1 named the next one, FRAME-SPLIT-0 named none and promoted nothing.
- **Windowless first.** Every law of the live editor was proven with no window in the proof (a mock surface, a
  scripted mouse, a counted clock) before a real window ran it. The host run then tests the host, not the law.
- **The first host run is an instrument.** LIVE-INPUT-0's first run received no key press; MOUSE-LOOK-0's first run
  received no mouse report. Each produced an amendment or a recorded unknown, never a patched claim.
- **Durability before vocabulary.** The session was made a saved, verified file before authoring grew, so every
  later host walk is an artifact another machine replays and not a transcript.
- **Mutation-test the rows.** A row is trusted after planted defects in the program each turn it red. Mutants that
  survived became new cases (ADMIT-0: a range fault with a trailing byte; an envelope on a move).
- **Count the readers.** Reading the code for READER-COURT-0 found four JSON parsers where three were believed,
  and a count of nesting depth that was wrong by one. Both were found by counting again, not by a failing row.
- **A court catches its author first.** The Python reader's fast path admitted `-0`; the registered case and the
  exhaustive court caught it before a row existed. And one earlier row was passing for the wrong reason until the
  gate began watching every refusal.

## Ghosts

What the gate does not prove is stated, graded and given the measurement that would settle it, in
[`docs/GHOSTS.md`](docs/GHOSTS.md). The ones a reader should carry from this page:

- Every wall-clock number is one host and one corpus.
- The live window's laws are proven over a mock; the host runs are few, and each is one run.
- The screen is read back at one composition in 75; a free-heading frame is checked during a run at one in 64, and
  exhaustively only at the save.
- A session's seal is a hash. It shows the file is whole, not who wrote it.
- The shell replays the session with its own copy of the workshop's fold; the two are held together by rows and by
  the workshop verifying every saved file.
- The two readers of the saved form have one author. Their agreement shows consistency; the verdicts written down
  before either existed are what stand against a shared mistake.
- No latency, frame-rate or feel claim is made for the live loop, and nothing is claimed about a model.

## Reading further

| Document | What it holds |
|---|---|
| [`docs/PROGRAM.md`](docs/PROGRAM.md) | the program in depth: the charter, the four layers, the frozen oracle, the RECORD-0 envelope, preregistration, the two-court rule, how a frame flows, the live session, admission, and the saved form |
| [`docs/GHOSTS.md`](docs/GHOSTS.md) | what the gate does *not* prove: every unproven assumption, caveat and soundness question, each graded and given the measurement that would settle it |
| [`docs/DEVNOTES.md`](docs/DEVNOTES.md) | dev notes: the optimization campaign (`GAUNTLET-0` to the `GAUNTLET-2` lock), the present-path courts, and the live campaign (`LIVE-LOOP-0` to `ADMIT-0`) — what each court found, the process rhythm, the lessons |
| [`docs/ROADMAP.md`](docs/ROADMAP.md) | where the program stands and the sequenced, falsifiable route: the live loop (built), admission (ADMIT-0 and READER-COURT-0 built), the declared design-event stream, and the presentation work beside it |
| [`verify/RUNGS.md`](verify/RUNGS.md) | the ledger: every seated rung, its rows, its grade, its limits, its falsifier |
| [`design/README.md`](design/README.md) | the design surface, content time: the five verbs, the design text, what is authority and what is a view, its limits |
| [`EPISTEMIC-INVARIANCE.md`](EPISTEMIC-INVARIANCE.md) | the author's isolation theorem, and the honest limits of its own formalism |
