<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The studio: a director summoned into the running plaza (STUDIO-0, STUDIO-1, STUDIO-2, STUDIO-3, MARK-0)

By the owner's direction of 2026-10-11: *"the LLM edits design intent; Verðandi compiles that intent into a live
world; the designer remains in control."* And by his ruling on how a model is reached: *"a pluggable model adapter,
with a persistent local director service behind it"*, starting with *"a CLI adapter so the first implementation
remains standard-library-only"*; *"the model proposes changes—it never directly mutates the live world. Verðandi owns
validation, compilation, preview, and admission."*

```text
 the page (art/web/play.js)          play.py                    art/studio.py, the gateway          a provider (a command)
 E target, R pin           ──POST──►  token, host  ──────────►  tags bound to objects
 Enter summons, @1 @2 …    ──POST──►  token, host  ──────────►  context from the head  ──stdin──►  the model, or a script
                                                                 limits, cancel, time    ◄─stdout─  ≤ 3 candidates (JSON)
                                                                 the response, read whole
                                                                 each candidate an intent ──► art/director.py: checks, scope
 [ Show ] swaps the scene  ◄──/live── candidates as sources  ◄── those not refused, compiled
 [ Admit ] [ Reject ] [ Undo ] ─────►  the director's ledger: evaluate, admit / refuse; the brief written
```

## Using it

```
python art/play.py plaza-night --director art/providers/scripted.json
python art/play.py plaza-night --director art/providers/claude_code.json
python art/play.py plaza-night --director art/providers/anthropic.json
```

The first needs no model: `art/providers/scripted.py` answers a selected canopy with three fixed variations (the three
of the owner's sketch: *Monolithic*, *Lit underside*, *Deeper canopy*) and anything else with nothing. It reads a
prompt only for the word *magenta*: it understands nothing, and is there so that the studio can be tried and tested.

The second asks a Claude model through Claude Code's command line (`claude -p`), on the login Claude Code already has:
no key is set for it. By the owner's ruling of 2026-10-11 it is the first real provider, for his own development
setup, *"not a substitute for a properly authorized provider integration in a product offered to other users"*. Its
settings, both optional, are in the environment: `VERDANDI_DIRECTOR_MODEL` (as `claude --model` takes it, an alias
such as `sonnet` or a full name; Claude Code's default if not set) and `VERDANDI_CLAUDE` (the executable, if `claude`
on the PATH is not it; on Windows `claude.exe`, since a `.cmd` or `.ps1` shim runs only under a shell and is refused).

The third asks a Claude model through the Anthropic Messages API, with a key from the Claude Console. The key is in
the environment, never in a file: `ANTHROPIC_API_KEY`. The model is the configuration's (`art/providers/anthropic.json`
passes `--model claude-opus-5-5`, the model his Claude Code CLI answered as, so the two providers differ in the adapter
alone; B1, 2026-10-12); `VERDANDI_DIRECTOR_MODEL` overrides it, and `VERDANDI_DIRECTOR_API` names another endpoint. The
answer is constrained by structured outputs (`output_config.format`, a JSON schema; the JSON is the answer's text), not
by a forced tool choice, which every current model refuses with 400; the schema sent is the gateway's with what
structured outputs do not support moved into its descriptions, and the gateway still enforces every limit. A refusal
or an answer cut at its token limit is said and not read.

The two model providers tell their models the same thing (`art/providers/director_prompt.py`: one system text, and the
request rendered as text), and differ only in how the model is reached.

```
python art/studio.py probe art/providers/claude_code.json
python art/studio.py probe art/providers/claude_code.json --references
python art/studio.py report
```

`probe` is the owner's smoke test, *"that the model was actually invoked—not just that a provider configuration was
loaded"*: it asks about the same canopy with two different prompts, through the gateway as the page asks, records both
requests (marked as the probe's), admits nothing, and says SHOWN only if the provider reported a model and tokens for
each and no two prompts were answered with the same revision lines. The scripted provider is NOT SHOWN, by design.
`probe --references` is STUDIO-1's measure, the owner's acceptance criterion put to a model (*"the model consistently
identifies the intended objects, receives their actual geometry, and proposes edits the existing compiler can
express"*): the north canopy the target `@1`, the west and south canopies pinned `@2` and `@3`, four prompts that each
name what to change (*make @1 match @2*; *make @1 twice as deep; keep @2 and @3 exactly as they are*; *give @2 a warm
glow along its edge, and leave @1 and @3 alone*; *make @1 look like it connects to @2, without changing @2*), each asked
twice (`--runs N`); for every candidate, which tags it changed and how many untagged objects, against what the prompt
meant, and its verdict. Each request costs a model call. `report` reads every recorded request of the brief and gives, by provider configuration, what the owner asked to
compare: the requests answered, invalid outputs, timeouts and provider errors, the provider's time (median and
longest), the candidates' verdicts, the edits admitted from the page, the tokens, and the cost where a provider reports
one, per admitted edit.

In the page (since STUDIO-3 the page opens in the editor; **P** plays, and in play what follows is what is under the
crosshair; in the editor it is what is selected): what is under the crosshair is named in the corner, by its address
(`plaza/canopy/19,10-28,11`) and its tag if it has one. **E** makes it the target; **R** pins it as a reference, or unpins it, up to four (the game's reset
is **Backspace** here). play.py gives each a tag, `@1`, `@2`, …, which names that object, and keeps it across restarts; each
tagged object is framed and labelled on screen (the target amber, a pin dashed blue), and the panel lists them with
their addresses, sizes and statements' lines. **Enter** opens the director's panel, and the game goes on. Type the
change, naming objects by their tags (*make @1 match @2*); **Ctrl+Enter** asks. The candidates come back with their
verdicts and what each touches (*@1 changed · @2 unchanged · no other object changed*). **Show** draws one in place:
the scene changes, the game, the player and the camera do not. **Original** draws the brief. **Admit** writes it
through the director's ledger, **Reject** records a refusal, and **Undo** admits the last admission's exact inverse.
**Cancel** stops a request, and **Esc** goes back to the world. Without a target, the prompt is for the whole world.

## The shell (STUDIO-3, 0230)

By the owner's plan of 2026-10-14 (Sprint 1, *"Core studio shell"*: *"Launch Verðandi, enter the world, select an
object, inspect it, and play"*), the page is a studio around the play surface, after his mockup: a menu bar (File, Edit,
View, World, Tools, Build, Play, Validate, Help; on its right **Local Build**, **Play (1080p)** and **Validate**), a bar
naming the scene (the world), the layer and the selection, with what play.py says (connected, the world, the ledger's
revision, the source drawn and its scene, the rules), a navigator (World, Create, Content, Review), the viewport, an
inspector with the world's layers and settings, and a dock of the asset browser, the candidates and the ledger.

Nothing in the shell is the world. It reads what play.py serves and asks play.py to act, through the routes the studio
already had and three new ones: GET `/object.json` (what a picked box's object is, read from the scene and lineage of the
source drawn: its address, kind, region, boxes, materials, the mesh the scene names, whether it collides, the statement
that made it and how many objects that statement makes, its nearest wall; a box of the play geometry is the map's and
says so; nothing is bound and no tag is made), GET `/validate.json` (the art checks' rows as they were run when the
source was compiled, and its latest refusal if it was refused; read back, not run again) and POST `/studio/build`
(every source compiled again now, as the watcher does on an edit, with the page's token; what fails leaves the scene
before it drawn).

**The editor.** The page opens in it: a free camera (right-drag looks, the right button held with W A S D flies, Q and E
down and up, the wheel moves forward), the cursor naming what it is over, a click selecting it. The pick is the view's
arithmetic: the ray through the cursor's pixel and the nearest box it enters of the layers shown, the dressing, the
play geometry, the movers and the standing targets. The selection is drawn as its box, projected in blue on a canvas over
the picture; **F** frames it. **P** (or Tab, or the tool strip's last button) plays: the mouse is captured and the game's
keys apply, as before; **Esc** comes back to the editor at the player's eye. The game waits while it is not played.
**Play (1080p)** plays at 1920 × 1080, the window filled, the picture 16:9. **E** and **R** make the selection the
director's target or pin it; in play they take what is under the crosshair, as before. A box of the play geometry, a
mover or a target can be inspected, not tagged: it is the map's.

**The viewport.** The tool strip: select (Q) and measure (T: two clicks, the distance between the points the rays hit,
in plan and in rise); move, rotate and scale are drawn and not built, and say why (nothing in the editor moves the
world). The pills: Perspective (and Top and Side, telephoto cameras: the renderer draws in perspective only, and they say
so), Lit (the renderer's picture, with the dressing's wireframe or the play geometry drawn over it), Show (the grid of
cells, the regions, the spawns and targets, the tags, the statistics). The statistics are what the page measures and no
more: frames a second, the frame's time, the time to issue it (the GPU's is not measured), the draw calls the renderer
made (counted), its triangles, boxes and lights, and the canvas's size; video memory is *n/a*, since WebGL does not
report it.

**The panels.** The inspector: Transform (the boxes' centre and size, read-only; nothing is rotated), Static Mesh (the
asset the scene names, its source and licence), Materials (each with a flat swatch, a key and not the renderer's
picture), Collision, LOD, Physics, Gameplay Tags (the studio's tag) and Custom Properties (the statement, its key, what
it makes and can change, the nearest wall, the lights). Layers: each shown or hidden (the renderer is given the scene
without it; the game is not touched) and locked or not (never picked); the bar's Layer limits a click to one. World
Settings: the environment, the grid, the player's constants, the spawns, the regions, the views, the source. The asset
browser: the scene's own pieces by folder (the dressing by kind, the play geometry by kind, the movers, the spawns and
targets, the lights, the materials, the regions, the views, and the views saved in the page, each with the art
statement it would be), each drawn as a thumbnail by a second renderer from a camera framed on it: the scene as it
stands, from there. The candidates: the request's, each drawn the same way from the target's frame, with its verdict
(until 0249 *Ready* when CLEAN and undecided, the page's own judgement; since 0249 the host's account, admissible or its
first refusal, or *account pending* until it is given: DASHBOARD-0, below), its rung, and Show, Admit (since 0249 enabled
only by an admissible account of the revision the page last read) and Reject, which do what the director's drawer does (an
admission brings its still, as ADMISSION-0 requires). The ledger: `/history.json`, newest first, ADMITTED, CANDIDATE,
REJECTED, REFUSED, REBASED. The director's panel is a drawer over the inspector (Enter). A footer keeps the roadmap
in view: Sprint 1, the shell; then Mark & Shape, the candidate loop, a world-generation slice, the dynamic world,
scale.

What is not built says so, with why: Geometry (the layout changes through the design tool), Voxel Tools (the world is
cells and boxes), Decals (no statement), Audio (the studio cannot make it yet), AI (none), Prefabs (one statement makes
one object), Procedural (a later slice), Templates (a world is a duplicate of one). Stills (`?view`, `?cam`, `?still`) are the
picture alone, as before.

## Marks and shapes (MARK-0, 0231)

By the owner's plan (Sprint 2, *"Mark a wall, draw a doorway outline, save it, reopen it, and request an edit against
that exact region"*) and his second mockup. **M** (or the tool strip's shape, or Create ▸ Mark & Shape) turns the shell
to Mark & Shape: on the left the worlds and the layers (and the shapes), over the viewport the tabs Viewport, Top, Side
and Perspective, under it a toolbar (Select Q, Move W, Rotate E, Scale R, Add Point, Finish Shape, Cancel), on the right
the shape's inspector, and below the candidates with their M, C and P and a split of the world and a candidate.

**A shape** is the designer's mark, never the world. Add Point's first click on a surface marks it: the box the ray
meets (of the dressing, or of the play geometry; a mover or a target moves, and is refused) and the face it comes
through. Each click after it adds a point where the ray meets that face's plane, snapped to the face's edges within
15 cm and else to 5 cm (Shift draws free); Enter finishes, Esc drops it. A shape is an opening (subtract), an addition
(add), a region or a path (an open line). Its vertices are surface-local: metres along the face's u and v from its
origin, to the millimetre, in the frames `art/studio_marks.py` defines (seen from outside, u right and v up; on a top
face u east and v north). Q selects a shape (a click inside it) or a point of the one being edited; W moves a point, or
the whole shape; E rotates it and R scales it about its centre, on its face; the inspector's table edits a point's u and
v, inserts a point after the selected one and deletes one. Nothing is kept until Save.

**Saved** through `POST /studio/shapes/save` with the page's token, in `art/ledger/<brief>.shapes.json` (VERDANDI-SHAPES
0, the canonical bytes of DIRECTOR-0, integers as strings, written whole under the content lock; a file that cannot be
read is never overwritten). The host checks every save against the scene served now: the anchor must name that scene
and a box of it with exactly the coordinates the page saw (SHAPE-STALE otherwise: mark it again), a coordinate is the
decimal written (the body is read with its numbers as decimals; NaN, Infinity, a key twice, more than three decimals
refused), a closed shape is simple (no zero-length edge, no fold, no two edges that are not neighbours meeting, an
area), and every vertex is on the face unless the designer unticks *Keep within surface bounds*. `GET /shapes.json`
gives each shape's status against the scene served now: *ok* (its box exactly as marked: every vertex where it was in
the world), *changed* (the box moved or changed size; the vertices are read again on the new face, and if the marked
face itself did not move that is said), *gone* (no box of its id), *ambiguous* (two boxes share it). A shape is never
moved to another surface.

**Constraints.** Two are checked by the host, exactly, and marked HOST: *Keep within surface bounds*, and *Maintain
player clearance (≥ c m)*: on an upright face, an opening admits an upright rectangle as wide as a body (2 r) and c
tall standing within a step of the face's foot (a body walks through it), an addition one anywhere in it; decided over
a finite set of positions that provably contains one if any fits (`admits_rect`, its comment says why), up to 16
vertices (beyond, NOT CHECKED, said). The others, *Preserve structural supports*, *Update collision* and the material,
are WORDS: the director is told them, and nothing checks them.

**The director.** A prompt names a shape as `#name` (the drawer lists the shapes; a click puts one in). The gateway
reads each named shape against the head as the files stand and sends it in a request of version 2 (below): a name no
shape has, or a shape not *ok* at the head, refuses the request (STUDIO-SHAPE). The scripted provider answers an opening
or an addition in the play geometry UNSUPPORTED, `layout.change` (the art cannot change the map), and a shape on a
canopy with no target as if that canopy were the target; a model is told what a shape is and that it is where the
designer means. A queued task's shapes are read when it runs; a reviewed one says which of its shapes are no longer ok.

**The candidates and the split.** Each candidate card has M (the look: materials, lights, the air), C (the play: the
collision, the movers, the targets; a CLEAN candidate of the art never changes it) and P (the placement of the
dressing: a box added, removed or moved), the host's since 0235 (below). The split draws the world (source [0]) and the
chosen candidate from one camera (framed on the request's shape, from the side its face looks to), with a slider;
**Compare** shows it larger.

What the shapes do not do yet: change the play geometry (no opening is cut).

## The candidate loop (HELD-0 and COMPARE-0, 0235)

By the owner's plan (Sprint 3, *the candidate loop*: candidates held to marked regions, compared, Preview and Diff,
iterated), on what MIXER-C prepared beside 0230 and 0231.

**What a candidate changed** is the host's, said once (`art/scene_diff.py`). Its evaluation's two scenes, the head as
the files stood when it was evaluated and the candidate, are compared by identity (a record is its id, an object its id
with its parts, never matched by likeness), field by field as the bytes the exporter wrote: a diff whose inverse is the
diff read backwards and which applied to its base gives the candidate, and to anything else is refused. M, C and P are
read from it, each raised exactly when its part of the scene changes (the self-test checks them against projections of
the scene written apart). The page shows them and computes none.

**Held.** A shape's region is its outline swept along its face's outward normal, from the back of the marked box out
to the shape's *reach*: by default to the sky on a top face (what stands on a floor rises from it) and 1 m on any
other (what hangs on a wall or under a canopy); an opening runs on through its box, as far again behind it (at most
1 m). The inspector's *Region* sets the reach (blank: the default). For each shape the prompt names, every box the
candidate adds, removes, moves or repaints (a material changed counts every box made of it; a light its fixture; a
mover its whole travel) is related to the region exactly (inside, crossing, touching, outside, over the decimals the
scene states), and the candidate's verdict is **held** (every change inside), **adjacent** (nothing beyond the
region's boundary, something on it), **outside** (something beyond it, or a change of the whole world: the air, the
play), **missed** (it changed things, none in the region), **empty** (nothing physical changed) or **stale** (the shape
is not as it was marked in the candidate's base: mark it again; never re-read). The request tells the director the
region and, at the head, which statements make objects wholly in it and which reach it with objects outside it; nothing
the director says about where its change lands is believed.

**The order.** The candidates are shown in the host's order, lexicographic and by host facts alone: the director's
verdict (CLEAN, then LEAKAGE, then the rest), the region (the worst of the shapes' verdicts: held, adjacent, outside,
missed, empty, stale; no report last), the play changed for a request of the art (C) after unchanged, the objects not
held, how much changed, the letter. A title or a rationale never enters it.

**Diff.** The split's **Diff** outlines, over both pictures, every box the account names (GET `/held.json`): before the
change dashed, after it solid; with a shape named, each coloured by its relation to the region (inside, touching,
crossing, outside), else by what happened to it (added, removed, changed).

**One or none.** Admitting a candidate records, on its line of the request's record, the set it was chosen from: what
was shown, the host's order, each one's region verdicts, the one chosen and those not chosen; those are marked *not
chosen* and stay undecided (rejecting one still writes its refusal to the ledger; admitting one is refused, the head
having moved). **None** (on the candidates' bar, POST `/studio/none`) marks every undecided candidate *none chosen* and
records the set rejected in one line; the ledger is not written and the world is as it was. Each candidate's whole
report is kept beside its intent (`<letter>.held.json`), named by its sha256 on the request's line.

Not done: a region drawn as a volume in the viewport (the inspector says the reach); the light a held lamp casts beyond
the region (a light is its fixture's box: NOT_MEASURED, said); finer verbs where a statement makes many objects (a
request whose statements reach the region only with objects outside it is told so, and its candidates read outside).

## A building's bays (FACADE-0, 0237)

A building's facade is a grid of pieces, one for each bay of each floor of each side that looks onto open cells
(`building:x0,z0-x1,z1:s-b3-f2` is bay 3 of floor 2 on the south side), and a `bay` statement changes one of them and
nothing else: a window, a panel, or blank. A shape drawn on one bay of a side and asked about is held by a candidate
that changes that bay alone. The scripted director answers a shape on a building's side with three candidates: the bay
under the shape's middle panelled in the building's own material, the same bay left blank (both held), and that bay
panelled on every floor (outside: it reaches the floors above and below). An undo is the bay statement taken away.

## Region-strict admission (STRICT-0, 0238)

A request may be **strict** (the drawer's *Strict: held only*, or `"strict": true` with POST `/studio/ask`). It must
name at least one shape (STUDIO-STRICT otherwise), and the director is told it is strict. Each candidate then carries
the host's strict check (`art/scene_diff.py` `strict`), computed from the two scenes of its own evaluation like its
account: its **receipt**, every box it changes (a changed piece is two boxes, as it was and as it is), each with the
shapes whose regions hold it; its **inverse receipt**, the same for the change back; and its verdict, **PASS** when
every box lies inside at least one named region and nothing changes the whole world (the air, the tops, spawns or
targets), else **ADMIT-OUTSIDE** (a box outside every region, or a change of the whole world), **ADMIT-EMPTY** (nothing
for a region to hold) or **ADMIT-STALE** (a shape not as marked). The whole check is kept beside the intent
(`<letter>.strict.json`), named by its sha256 on the request's line; the card shows *strict PASS* or *strict FAIL*
with the boxes outside, and Admit is off for a FAIL. Admitting checks again, from the admission's own evaluation and
never the card's: a FAIL is refused with its code and the refusal is a line of the request's record
(`admit-refused`); a PASS is admitted with the check in the ledger's admit event (`region`: the shapes, the sha256 of
their records, the receipt and the inverse receipt, each with its sha256), and the director refuses a strict admission
that brings no passed check or no receipt. Undo is the exact inverse revision, as ever; the change it makes is the
inverse receipt, box for box. A request that is not strict is as it was: its held accounts inform the order and the
designer and refuse nothing. The queue's requests are not strict.

## The impact panel (IMPACT-0, 0239)

Every candidate carries what it costs the native renderer (`art/web/scene_render.js`) against the base of its own
evaluation, computed by the host (`art/impact.py`) and kept beside its intent (`<letter>.impact.json`, named on the
request's line): the triangles (every play box and piece of dressing a box of twelve; a target ten, a mover twelve),
the draw calls of one frame (all static triangles are one call a pass), the lights the renderer draws (the first 160)
and their candelas, the bytes of the textures it builds from the scene (the lights, their visibility per cell, the
height and roof fields; the scenes carry no image), and one frame's milliseconds, an **ESTIMATE** from those counts by
the linear model in `art/impact_model.json`, whose coefficients are the exact least squares of its calibration rows,
each row a scene drawn by the renderer on the host and date the file names. The card shows the differences and the
estimate's; its tooltip (*how computed*) gives the terms, the calibration's host and date, the counts, the preview's
path, the director's words for why (not checked) and the provenance (the provider, its model, the prompt's sha256,
the request, the seed). Budgets (`impact_model.json`) are advisory: a candidate over one reads *over budget
(advisory)*, and nothing is refused for it. *ADVISORY ESTIMATE — not admission evidence*: no verdict, order or
admission reads any of it. The preview's camera path is named and seeded by the request (eight poses round the first
shape, or the target, at 14 m), the same for every candidate of the request.

## The preview in motion (PREVIEW-0, 0240)

*Preview* on a candidate's card plays the base and the candidate along the request's camera path (IMPACT-0's, named
and seeded by the request, the same for all its candidates) with one seeded simulation, and shows them side by side.
The host plays (`art/motion.py`): the graybox's own tick under rules 3, in its Python twin `graybox/tick_ref.py`, from
spawn A, driven by an actor whose next input (walk, strafe, turn, jump, back, stand) is drawn every 30 ticks from a
stream seeded by the request; 120 ticks a pose, 960 for the path's eight poses, each side from a world and a state made
new. Each tick's state is written canonically (the twin's snapshot, every mover's box, the world's identity, the
stream's counter) and its **state fingerprint** is that text's sha256: the canonical evidence. The page draws a still of
each side at each pose with the renderer it plays with (PNG, 480 x 270) and gives them to the host
(`POST /studio/preview/still`); the host reads each (an RGB or RGBA PNG, else `PREVIEW-STILL`), compares, and keeps.
The stills' SSIM (Wang, Bovik, Sheikh and Simoncelli 2004: an 11 x 11 Gaussian window of sigma 1.5, K1 0.01, K2 0.03,
on luma box-averaged to 96 x 54) and PSNR are **advisory**: a look, never a verdict.

Per pose, `comparison_result`: **PASS** (both states the same, both stills given), **DIFFER** (the states differ; the
report names the first tick that differs and its fields, e.g. `identity`, `movers`, `snapshot.x`), **INCOMPLETE** (a
still or a state missing: the report's code is `PREVIEW-INCOMPLETE` and it is never called *replayed*), **UNTRUSTED**
(`UNTRUSTED_IMAGE`: the candidate's earlier preview had this state with other still bytes; the renderer moved, not the
world). *State verified* only when every pose is complete and every state agrees. A candidate of the art, CLEAN at the
director, never changes play, so its states are the base's at every tick: the badge says so, and a DIFFER says the
candidate moved the play.

Kept beside the intent, named on the request's line by sha256 (`"decision": "preview"`):

| file | |
|---|---|
| `<letter>.preview.meta.json` | request, candidate, provider, model, prompt_sha256, camera_path_id, viewport, framerate (120), tick_count, seed, spawn, still_ticks, semantics, `made_at` (the one clock in it) |
| `<letter>.preview.states.tar.gz` | each side's state at every tick (`base.states.jsonl`, `candidate.states.jsonl`) and its fingerprints |
| `<letter>.preview.stills.tar.gz` | the stills, `<side>-<pose>-tick<tick>.png` (and `<letter>.stills/` for the page) |
| `<letter>.preview.report.json` | per pose: tick, state_fingerprint, image_digest, comparison_result, ssim, psnr; replayed, code, state_verified, first_difference, the provenance |

The archives are the same bytes from the same inputs (sorted members, every time and owner nought, no name or time in
the gzip header). Retention: 30 days by the meta's `made_at` (`art/motion.py gc FOLDER [DAYS]`, and at the end of every
preview over the brief's records); the request's line keeps the sha256 for good. Refusals: `PREVIEW-NO-PLAN` (no
export, or no preview under way), `PREVIEW-STALE` (the head moved since the candidate was drawn), `PREVIEW-STILL`. Off
the gate: nothing that decides reads a preview.

## The camera path and its rule (PATH-0, 0241)

The preview's path (`art/camera.py`, through IMPACT-0's `camera_path`) is held to one rule, decided exactly (rational
arithmetic from the numbers as the scene and the path write them): every box of the scene is an obstacle (its play
geometry, its dressing, every mover over its whole travel, every target's column); a pose is clear when it is at least
0.5 m from every box in the max norm and 0.5 m above the ground plane; the segment between two consecutive poses passes
inside no box grown by 0.5 m. Sight (each pose's line to the focus, its last 0.75 m left out, inside no box) is recorded
for each pose, not required. With a shape, the path is an arc of eight poses over 120 degrees in front of the shape's
face, one radius and one rise all round (the first of 14, 11, 17, 8, 20 and 5 m, and 6, 4, 9 and 2.5 m, that clears
every pose and every segment with every pose seeing the focus; failing sight, the first that clears); without one, an
orbit of the focus; failing both, each pose on its own, one that cannot clear left out and named. Fewer than four clear
poses: no path (`CAMERA-PATH-NONE`), and the preview refuses (`PREVIEW-NO-PATH`). The same scene, focus, face and seed
give the same path, byte for byte. The path is made at the head and held to the rule again against each candidate's own
scene when it is previewed (`path_check` in the plan and the report, shown in the dialog), never moved for one. A
request drawn again (`restore`) makes its path again from its recorded shapes, and each drawn candidate's impact again.
The rule is geometric: it says nothing of how well a pose frames its subject, which a person judges by eye. A world's
reference (`python art/quality.py freeze NAME`) is its scene's bytes at an exporter, so that ART CHECKS see a changed
exporter or platform; it approves nothing visual. A world's views are a visual baseline only when the owner approves
them: the foundry yard's eight (0241's contact sheet) are provisional until B5b's framed comparison.

## The flagship's acceptance (FLAGSHIP-0) and a path framed for its subject (FRAME-0), 0243

**Framing.** When a request's shape lies on an upright face, its arc is framed for the shape's region (the rectangle
round its vertices on the face): of the rings that hold PATH-0 with every pose seeing the focus (radii 5 to 20 m, rises
2.5 to 9 m), the one whose smallest view of the region is largest, provided that at every pose the region's four
corners are inside the still less 5% at each edge, at least half of it is seen (exact occlusion, sampled 0.1 m in front
of the face, before a bay's 4-5 cm) and it covers at least 24 x 24 pixels at 480 x 270. The framing is decided in
floats to choose and exactly to record; it is said in the path (`framing`: met, each pose's area, share seen and box
on the still). When no ring frames it the path is PATH-0's plain arc and the framing reads `FRAME-NONE`: the path is
never loosened to meet a framing. The path is made in the request's own thread and is the same for every candidate; at
a preview it is framed again against each scene (a candidate may hide or move what it frames), and the dialog says so.
The thresholds are engineering proxies (LEGIBLE-0's), not perceptual legibility.

**The sheet to inspect.** When both sides' stills are complete, the host writes `<letter>.preview.compare.png`: at
each pose the base's and the candidate's stills at half size and, when the path frames a subject, both crops of the
subject (its box on the still and a fifth round it) enlarged side by side, then their difference eight times over (where
the candidate changed the picture, however faintly); named on the request's line by its sha256
and shown under *Inspect* in the preview's dialog. A picture for a person, not evidence: SSIM stays a look.

**The flagship's acceptance.** `python art/flagship.py selftest` (or `python art/play.py --flagship-selftest`): in the
foundry yard, with the scripted director, the marked bay's edit through the studio's own HTTP surface, each stage's
evidence required before the next: *mark* (the region on the warehouse's face, ok), *request* (strict, tied to the head
it was asked at), *candidate* (held, strict PASS, its impact present), *preview* (one path for every candidate, clear
and framed in both scenes; replayed, every state verified), *admit* (the ledger's admit event from the request's head
to the files' head, with its region receipt), *undo* (the head, the brief's bytes and the scene's bytes as before). The
first stage without its evidence stops the procedure with its code (`FLAGSHIP-MARK`, `-REQUEST`, `-HELD`,
`-NO-IMPACT`, `-FRAMING`, `-PREVIEW`, `-ADMIT`, `-UNDO`) and nothing further is asked of the studio. The procedure is an
acceptance: the studio's own admission still reads none of the impact, the framing or the preview.

**A visual baseline** is the owner's act, apart from the scene's bytes reference: `python art/flagship.py approve
WORLD REQUEST LETTER --note TEXT` appends to `art/visual_baselines.jsonl` the sha256 of a preview's files (its meta,
report, archives and sheet), its path and subject, and his note, only from a preview that is complete, every state
verified, its path clear and framed in both scenes; refused otherwise, and without a note.

## Certificates (CERT-0) and glue (GLUE-0), 0244

**Every admission's certificate.** After each admission and each undo the studio writes, by the ledger's sequence
number, `art/build/studio/<world>/certificates/<seq>.json` (`art/certificate.py`): the parent (the head before and its
parts), the operation (its revision lines), the inverse (the ledger's), the child (the head after and its parts), the
statement keys it touches, its provenance and the ledger event it is made from (its sha256). The ledger stays the
authority. The certificate is checked at once against the brief as admitted, exactly and without exporting anything:
the child's text is the child's, each head is its parts', the change is the art's alone, and the inverse applied to the
child gives the parent byte for byte (`exact`) or, failing that, its statements token for token (`statements`: the
same scene, the head not). The request's line and the admission's answer carry the summary; an undo's answer says
whether the head before the admission came back (`head_restored`). Found by it (0244): an `=` on a statement written in
aligned columns, and every `-`, are undone statement for statement but not byte for byte (the line comes back in single
spaces; a removed statement comes back at the end, without its comment), so the head after such an undo is not the head
before, though the scene is; only `+` and `=` on single-spaced statements are exact. Corrected at 0245 (MEASURED on his
machine, by round trips of `apply_revision`): the exact cases are narrower and not quite those. `+` is exact only on a
brief that ends in exactly one LF; `=` only on a single-spaced statement whose comment, if any, follows exactly two
spaces; and `-` of the last statement is exact too when that statement is single-spaced with no comment, the brief
ends in exactly one LF and the line before it is not blank, while `-` of any other is not. On today's briefs: harbor-day, harbor-lift and plaza-night end in a single-spaced statement, so a `-` of their last
statement and its undo give back the head; foundry-yard's last line is aligned, so on it no `-` does.

**Glue.** `art/glue.py` judges two edits written against one head: they *commute* when both orders apply and give the
same scene, and they *glue* when, besides, the glued scene changes exactly what each changes and both agree on every
section they both change (a section: a piece by its id, a material by its name, the environment; the provenance field
`by` left out). Otherwise the pair is OBSTRUCTED, and its obstruction is an object with a sha256 the same whichever
edit is named first: which orders would not apply, where the orders differ, where the two disagree. `python art/glue.py
census` judges every pair of seven of the flagship's edits. Nothing in the studio decides by it yet.

## The ledger held (LEDGER-SAFE-0), 0245

**No event over a head the ledger does not hold.** An evaluation, an admission or an approval names the head it was
checked against. Each is now appended under the tree's content lock, and only while the files are the head the
ledger replays to and that head is the one it was checked against (`held_head`, `append_checked` in
`art/director.py`). Otherwise it is refused and nothing is appended:
- `LEDGER-UNLOGGED`: the files changed outside the loop (a hand edit, a new exporter). Record the change first, after
  reading it: `python art/director.py rebase BRIEF --note TEXT` (with `--root` for a world of the desktop studio).
- `HEAD-MOVED`: another writer's change landed between the evaluation and its append (the studio's admit, reject and
  undo evaluate before they take the lock). Ask again.

Before 0245 one such event made a ledger that replay, and therefore rebase, refuses for good (MEASURED on 2026-10-16
on a copy of the checkout's plaza-night, whose files its ledger did not hold: UNLOGGED-CHANGE, the likely cause 0237's
exporter recorded by no rebase, INFERRED; the owner's desktop worlds harbor-day and plaza-night were unlogged too, on
copies). The live loop still serves a hand edit as it
always did; only the writers of events that name a head wait for it to be recorded (a `refuse`, which names none, is
appended as before; the studio's reject is held by the evaluation it appends first).

**A rebase records only what the checks pass.** `rebase` reads, replays and appends under the lock, first recovering
a dead writer's half-done admission it finds there (completed if its admit event is in the ledger, undone if not). It refuses files that fail any of the art checks an evaluation runs
(`REBASE-CHECKS`, naming them; the frozen reference is not one of them, as for CHECK-FAILED) or that the exporter refuses (`REBASE-EXPORT`), and keeps the
checks it ran in its event. Replay holds a rebase's text to the art its parts name (`LEDGER-REPLAY`), and refuses one
recorded with a failing check (`LEDGER-REBASE`).

**At the studio's boundary.** A director refusal reaches the page as `STUDIO-DIRECTOR-REFUSED` with the director's own
code (`director_code`: `LEDGER-UNLOGGED`, `HEAD-MOVED`, `ADMISSION-0`, `SHARED-MAP`, …); before 0245 it reached the page only inside the message's text, never as a field of its own.
A certificate is written whole (`durable.write`). Every art admission the ledger holds without a certificate is given one
at the studio's start, from the ledger alone (`recover_certificates`): the one a crash left without (the studio writes
it after the admit event), and those it never certified (the command line's, those from before CERT-0). Its provenance
says it was made from the ledger, since the request's is not in it; a certificate that cannot be made is not, and the
start goes on. An evaluation's append first recovers a dead writer's half-done admission it finds under the lock, as a rebase does. A studio route with no
branch is refused (`STUDIO-ROUTE`); before 0245 the undo was the last line every unmatched route fell to.

## The page executed by a test (PAGE-0), 0246

Before 0246 no test ran the page's own script: the suites called the studio's routes from Python and gave it synthetic
stills. `python art/play.py --page-selftest` (also `python art/page_test.py selftest`) makes the flagship's edit
through the page, in a real browser, headless, with a throwaway profile: on Windows Edge, then Chrome; elsewhere the
first of `microsoft-edge`, `google-chrome`, `chromium` and `chromium-browser` on PATH. `--browser EXE` or
`VERDANDI_BROWSER` names another, and `--headed` shows the window.

**How it is driven.** The host lays the foundry yard in a scratch tree, serves it with the scripted director, and arms
a page test on its own server (`hub.page_test`). Only while one is armed does the server serve the driver
(`/page_test.html`, `/page_test.js`) and answer its channel (`POST /studio/page-test`, the studio's token); unarmed,
the driver is 404 and the channel is refused `STUDIO-ROUTE`. The driver holds `/play.html` as it always is, in a frame
of the same origin. It takes the host's steps one at a time and does each with the page's own controls:
- Enter summons the director;
- the shape's tag puts `#bay` into the prompt;
- Strict is ticked and Ask pressed;
- the card's Preview, Admit and Show are pressed;
- the drawer's Undo and Original are pressed.

Each control is pressed where it is: its centre is hit-tested first, and a control something covers is said, never
clicked through (lesson 75). The press itself is the control's `click()`, a synthetic event; the keys are synthetic too.
The camera for the admission's still is put where the request's own framed path begins, through `PLAY.cam`: a hook,
not a person's mouse; the view is held at that pose before Admit is pressed and after the page's word. The driver reports what the page showed: its status line, the toasts a person sees, a card's
buttons and chips, the preview's badge, the scene the view drew. It decides nothing.

**What holds each step is the host's.** After each step the host reads the request, the ledger, the certificate, the
preview's report, the scenes it serves and the stills the page gave it, read as PNG. The one exception is the opening,
which rests on what the page reports: its title (held against the brief's own), its director, its canvas and its slot.
A run ends at once when its page is lost: a step not answered, a browser that has ended, or the run's deadline passed
(700 s for the honest run and 200 s for each of the four plants' since 0248, 1,500 s inside the full check's 1800 s). Its rows are printed as they are
made. The preview's sixteen stills
(480 × 270) and the admission's still (the canvas, 960 × 540) are drawn by the native renderer: the first stills in any
suite that are not synthetic. Their detectors are read and printed, OBSERVED; a detector proves nothing.

**The plants.** Through the page, each showing its code in the page with the world as it was:
- a region refused: the host's strict check refuses the column (ADMIT-OUTSIDE, boxes outside), its card shows
  strict FAIL, and its Admit cannot be pressed;
- a failing preview (one run's state carried into the next): the host's verification fails, and the page's window says
  "states differ";
- a still the host never received: the page says `STUDIO-NO-STILL`, in its status line and its toast;
- a stale head (the brief edited after the preview): until 0249 the page said `STUDIO-STALE` after the press, in both;
  since 0249 the card shows the host's own `STUDIO-STALE` and its Admit cannot be pressed (a changed expectation: Admit is
  the host's account), and a row holds the refusal each card displayed (this one, and the column's ADMIT-OUTSIDE) against
  the host's own answer to Admit at the same revision.

Of the harness itself, each a whole run with its rows silenced:
- the page's Admit unwired, and a page that skips its still. Each is a served copy of `play.js` with one line changed,
  caught only when the admission's row fails; a plant whose line is not in `play.js` exactly once is not planted, and
  the suite fails;
- the driver pressing the Show of a card found before the page drew its cards again (0248), caught only when the Show
  and Original row fails with the admission and the undo passed, the world read fresh and the press refused as a
  control the page had replaced;
- the host's wait for the live loop taken away (0247), caught only when the Show and Original row fails with the
  admission and the undo passed, the hold met and the world read stale; the suite prints that row's detail.

**A control is pressed as the page stands (0248).** The page builds its cards again on every sync of its slots
(`shell.candidates` empties the list). The owner's run of 0247 failed at the press of Show, its error cut to "Show on
Pane". That the driver had found the Show before such a sync (no longer in the page, 0 x 0) is INFERRED, from reading
`press` and from a reproduction that gave the same words with a sync forced between the find and the press. `press` now
refuses a control no longer in the page by name. Before Show, the driver draws the cards again on purpose, by a hook
(`PLAY.slot(0)`, the function Original's button calls), so the redraw is met in every run, and it finds the card after
it, in the same step as the press, where nothing can redraw between.

**The live loop is eventually the files' (0247).** `play.py`'s live loop serves a write of the files one compile after
it sees it, a compile in a fresh process. Read too soon after a write, the world it serves is the one before it. The
owner's run of 0246 read it too soon after the undo, and its Show and Original row failed; a trace on his machine, by
the agent, met the same race in an ordinary run, its read 0.13 s too soon (MEASURED once). The honest run now holds the loop's recompiles closed from the undo until it has read the world served (the
admitted scene still), so the race is met in every run. It then lets the loop go, waits until the loop serves the
files' own head, and only then compares. The page is told the scenes the host serves: it draws the world first, then
presses Show and Original, and each press must make it apply a scene (its count of swaps grows), so that a press that
only chose a slot whose scene was already drawn does not pass.

**The browser's end.** On Windows the browser is started by a holder in a job of its own (KILL_ON_JOB_CLOSE, the desktop
studio's `Job`), and the run ends the holder. The holder also ends by itself when nothing but itself is left in its job,
so a browser that ended on its own is seen. Elsewhere the browser runs in a session of its own, ended as a group. On
Linux its first process also has PR_SET_PDEATHSIG, so the kernel kills that one process if the test's process dies
first (its other processes are not signalled; NOT_MEASURED, never run off Windows). The row then asks that nothing whose command line
names the run's profile is left. The query that says so must have found the browser's own processes while it ran (the
holder's command line names the profile too, so it does not count), and a query that fails reads as unknown, never as
nothing.

**What it does not show.**
- A person's judgement of the picture. The stills are held as PNG of the right size, unlike the window's at every
  pose, with their detectors read, and nothing more.
- The page's look: layout, colours, legibility.
- A real provider: this is the scripted director.
- The page's mouse look and play mode: pointer lock needs a person's gesture.
- Mark & Shape's drawing of a region: the host saves the shape, as FLAGSHIP-0 does, and MARK-0 holds the shapes.
- Timings: they are printed and never checked.
- The browser's ending off Windows: never run here.

Without a browser the suite fails: `art/selftests.py` has no skip.

## The dashboard (DASHBOARD-0), 0249: every panel says what it is of

The owner's conditions for the dashboard (2026-10-17, quoted in `docs/ROADMAP.md`) and his invariant: *"At the time a
panel claims to represent host revision H, its displayed facts must be derivable from H—or the panel must identify
itself as stale."* This is the cards half: the revision, the cards and their accounts, the dock's tabs (Candidates,
Queue, Validation, Evidence), Undo's proof and the wrong-world guard. The worlds and import are 0250's.

**The revision.** `/live` carries `rev` (VERDANDI-REV 0), read so that its halves agree (`Live._read`: the gateway's
state before and after the slots, equal, the live version unchanged and no request publishing; read up to four times
in all, and `read.consistent` false when they never agreed):
- the world and the server's process (`Hub.instance`, new at every start);
- the live version and each slot's scene, its head (from the exporter's lineage) and its latest compile's head, and for a
  refused compile the sha256 of its refusal;
- whether the files are compiled as they stand (`settled`: no compile running and every watched file's stamp as the
  watcher's last cycle saw it; `None` until a watcher has looked) and what is compiling;
- a digest of the files' stamps; the ledger's last line and whether an admission is half written (its pending folder);
- the request's identity (`state_sha256`: the gateway's state without a running request's elapsed time) and whether its
  candidates are being published;
- `id`, a sha256 prefix over all of it.

A comment changes the brief's head and not its scene: the live version now moves on a head too.

**How a panel says what it is of.** Each panel keeps the identities it was drawn from and, at each read of `/live`,
compares them with the host's: `current`, `stale`, `settling` (the host has not compiled the files as they stand),
`unknown` (play.py does not answer, restarted, its state was changing as it was read, or its watcher has not looked) or
`refused` (an answer for another world). The words are on the panel (`.pstate`) and in `data-state`. **Current is an
observation**: the identities were equal when the page last read them. It authorizes nothing; the host checks every press
again. The page computes no head and no account.

**A card's Admit is the host's account.** The account is admit()'s own predicate run dry, never a second policy (his
nuance of 2026-10-17): `Gateway._admission` holds the checks of an admission in admit()'s order, and `admit()` runs it
before it writes; `Gateway.account` runs it with `dry`, writing nothing, the still pending (the page takes it as Admit is
pressed; its presence and detectors are checked then) and the director's checks made as at the press
(`director.admit_dry`: append_evaluation's guard `held_head`, `cmd_admit`'s checks, now `admit_checks`, shared with
`cmd_admit`, and the commit's shared map), with a stand-in still the detectors flag nothing in. Its answer is the first
refusal, admit()'s code and the director's, or none: the checks after the first refusal are not reached, as at the press.
A worker per world (`Live.accounts_loop`, started when the page reads `/live` and stopped a while after it stops)
computes the accounts again whenever the revision moves, keeps them only if the revision did not move while they were
computed and no admission was half written, and `/live` carries them with the revision they are of. The page enables
Admit only by an account of the revision it last read that says admissible; otherwise the card says why (the host's code
and words, or that the account is being computed again). The "Ready" badge, the page's own judgement, is gone.

STUDIO's row holds the comparison: for nine planted states (admissible; decided; stale; the files ahead of slot 0 with a
candidate drawn at them; the files the exporter refuses; a hand edit the ledger does not hold; a ledger that does not
read; not drawn; LEAKAGE) the account `/live` displays is the refusal admit() answers at the same revision, with a clean
still given first, and each is the answer its state must give; two plants make the dry run differ from the press and are
caught by their own divergence. PAGE and PAGE-CARDS hold it through the page, in the same order: the clean still given
first, the card read once the page shows the host's account at the revision that makes, the revision read again just
before the press and after it.

**Evidence and EVIDENCE-0.** `GET /evidence.json?world=W&id=R&candidate=L` gives the admission's account (the same
dry run `/live` carries for the card, whose answer there enables its Admit; this one enables nothing), EVIDENCE-0's
checklist and the evidence itself, and writes nothing; it never opens a world (one not open is STUDIO-WORLD), and its
refusals name their world. EVIDENCE-0 version 0 applies FLAGSHIP-0's own predicates (factored out of `flagship.run`,
unchanged: `held_ok`, `strict_ok`, `impact_ok`, `clear_ok`, `framed_ok`, `preview_ok`) and its run's conditions on a
preview (framed in both scenes when the request names a shape, the path's subject; the candidate's path the plan's) item
by item over what the host keeps of the candidate; what does not apply to a request (no shape, not strict) is said so. It
is advisory: Admit reads none of it, it never says "accepted", and it is not FLAGSHIP-0's acceptance (AGENTS.md:
IMPACT-0, PREVIEW-0, FLAGSHIP-0). A card's line says how many items are missing. The answer carries the revision before
and after it was computed, and `moved` when they differ.

**Undo proves restoration.** The strip's Undo (`#mb-undo`, static: never rebuilt with the menus) and the Edit menu's
"Undo admission #N" name what the host would undo (`GET /undo.json?world=W`; its certificate the kept one checked, when
it is that event's own, else one made from the ledger and not kept: a GET writes nothing). Whether Undo would be refused
is undo()'s own checks run dry (`Gateway._undoing`, as the admission's account): the target's (nothing to undo; a layout
admission), the director's guard and the inverse's evaluation, and `cmd_admit`'s checks with the inverse it names; a
STUDIO row holds what it says against the press at the same revision. It is read again whenever the host's revision
moves (the ledger or the files), and says nothing it cannot foresee (a dead writer's half-done admission, which the
press recovers first). The press names the admission the page showed it as undoing; the host records that and whether it
is the one undone, and refuses nothing on it (the binding is a later patch's). The POST's answer carries `restoration`,
from the ledger alone (two replays): the head before the admission against the head after the undo, the art's bytes and
its statements, the parts that differ, the undone admission's certificate (made from the ledger and kept by the POST
when there was none). Its verdict is `exact`, `statements-not-bytes` or `not-restored`; or `unknown` when the undo is in
the ledger and its proof could not be read, which is said with the reason and never answered as a failed undo. The page
says `undone: … · restored exactly` only for `exact`; for `unknown`, that whether it restored is NOT KNOWN; otherwise
NOT restored, with both heads and what differs, in its status line and its toast. The restoration chip says so too:
while no event has been appended since and the loop still serves the head the undo was made at (`undone_at`), that the
world drawn is still the admitted scene; once the ledger or the files moved on, that the world has moved since the undo.
The undo's own certificate (a redo's inverse) is another thing, never shown as the restoration.

**Validation, Queue, Compare, the preview's binding, the stats.** Validation is a tab, read again whenever what is served
changes, and it leads with the latest compile's refusal (its rows labelled as the scene before's). The Queue's list moved
into its tab. Compare is in the bar in every mode and says whether Current is the candidate's own base scene, from the
host's identities. The admission's still and each preview still name the scene the page drew; the host records it and
says whether it was the candidate's (or the plan's); nothing is refused on it (binding is a later patch's, his ruling).
The stats say they are a software timing of the page's clock, with the clock's step; VRAM stays `n/a`.

**Another world's answer is refused.** The reads the page draws name their world (`/live`, `/validate.json`,
`/evidence.json`, `/undo.json`, `/history.json`, `/object.json`, `/held.json`, `/shapes.json`); one for another is
refused, said and not drawn (`answerFor`). The new routes require their world (`STUDIO-WORLD` without it, or for one this
server has not open). The answers to the page's own POSTs name none: the page posts them with its world, and they are
held by the host's own checks, not by `answerFor`. The page's world is the one it was served for (`data-brief`), never a
query's.

**PAGE-CARDS** (`python art/play.py --cards-selftest`, `art/page_dash.py`) executes this in a real browser, as PAGE does,
in six scenarios on one tree and one browser: the page opened before the host settled (case 1); the cards, their names and
accounts, the head moved after a card was drawn with the loop held and then let go (case 2), Compare; Validation failing
while an old pass stood (case 3); evidence missing though the card is admissible (case 4) and the Queue tab; Undo after a
command line's admission of an aligned statement (case 5a), after a change recorded between (5b), and the files restored
by hand but not the ledger's head (5c); another world's answer (case 7). Seven plants, each a copy of `play.js` with one
line changed, are run in their scenario and caught only by the row each names (two of them case 2a's), with every row
before it passed. Each step that decides a plant's row waits only for what that plant does not change (the host's
revision, the host's new answer), so that the plant fails its row at once, not by a wait running out; other steps wait for
an expected value, and a regression there fails its row when the wait runs out, inside the step's limit and the run's
deadline (720 s honest, 150 s a plant, 1,500 s the whole suite). A page that does not open says what it held (its
scripts' globals, and what its document was answered, from its resource timing) and what the server answered while the
test was armed (`Channel.served`, PAGE's open too): one opening of thirteen did not, in each of two full checks on his
machine, its `play.js` failed by a network error the second time, the cause not known (docs/ROADMAP.md, 0249).

**What it does not show.**
- That an account holds at the press: it is of its revision, and the press checks again under the content lock.
- That `settled` sees a write that keeps a file's mtime and size, or a write before the watcher's first look; or an
  input the export reads that the watcher does not watch (since 0249 it watches, besides the brief, the maps and the art
  layer's own code, the files the art checks read: `graybox/web/sim.js`, `graybox/tick_ref.py`, `art/web/scene_render.js`).
- That the stills are bound to their scene by the host: recorded and said only, until the binding's patch.
- A person's reading of the page; its look; timings (printed, never checked).
- The worlds, the outliner and import (0250), Linux, browsers other than Edge (Chrome is in the finder and never ran).
- Three paths no row exercises, VERIFIED BY READING only: an account, or Undo's, with an admission half written by a
  writer that ended (`not_foreseen`, Undo's `can` null); a restoration that could not be read (`unknown`); the press
  naming an admission other than the one undone (`page_saw.matched` false).
- The repair of the server's traceback on a hung-up idle connection: VERIFIED BY READING; no row exercises it.

## Legibility along the path (LEGIBLE-0, 0241: one test of Meaning-to-View)

`art/legibility.py` asks whether the evidence for a piece survives the view: along a path, at each pose, the share of
a 5 x 5 grid of points on the piece's outward face that is framed and seen (occlusion by camera.py's exact test), the
face's area in pixels at the preview's 480 x 270 and 66 degrees, and the WCAG 2.x contrast ratio of the base colours of
the piece's material and the surface it is set in. A pose reads the cue when at least half the face is seen, its area is
at least 24 x 24 pixels and the contrast at least 3:1 (thresholds declared and borrowed from screen standards, not
fitted). A **proxy**: no lighting, emission, reflection or hue, never a claim of what a person perceives, and nothing
that decides reads it. Not yet on the cards or in the request's record; its self-test measures the flagship.

## The references (STUDIO-1)

By the owner's ruling of 2026-10-11: *"Bind references to a scene revision and object identity, not just a reusable
tag. If an edit invalidates a reference, report it rather than silently redirecting it."*

- **An object** (`art/studio_refs.py`) is a box of the scene's dressing with its parts: an id that extends another by
  `:something` is a part of it (a canopy's ribs, downlights and edge fixtures, a tower's cornice), and a light belongs
  to the object whose id it shares. An object's identity is its id, which holds its cells: a canopy given new corners
  is a new object.
- **A tag** is made the first time an object is selected or pinned, and names that object, by its id; it is never
  given to another. B1 (docs/STUDIO-CONTRACT.md §9): the tags are kept in `art/ledger/<brief>.tags.json`, written whole
  and flushed, so a restart keeps them; the counter only grows, so a tag is never reused; a tag whose object is gone
  stays, listed apart. The panel shows every tag as a chip, and a click puts it into the prompt; a prompt naming a tag
  that is not the target or a pin is refused with what that tag names and how to pin it. A probe keeps no tags file. Selecting or pinning it again binds it again to the scene and head of
  that moment. Its status, in the panel and in `/live`, is read against the scene served: *ok*, *changed* (the same
  object, another shape or look than when it was bound), or *gone* (no object of its id). HARDEN-0 (0232): the tags
  file keeps each tag's object's fingerprint as it was bound, so a tag read back after a restart is as it was; a tag
  from a file before 0232 reads *unknown* until it is bound again (it read *changed*, and the model was told so, every
  restart: MIXER-C's finding), and the request says its change is not known.
- **A request** carries the target and the pins (below). A prompt that names a tag that is neither, or a tag whose
  object is not in the scene at the head, is refused before anything is asked (`STUDIO-REFERENCE`).
- **What each candidate touches** is the gateway's own account, from the director's verdict (what it realized and
  what a changed material affected): each tag changed or unchanged, the untagged objects of the head it changed, and
  the objects it made that the head has not.

## A provider's configuration

```json
{"provider": "cli", "argv": ["{python}", "art/providers/scripted.py"], "model": "scripted-1", "timeout_s": 30, "max_output_bytes": 65536}
```

`argv` is a list of arguments, run from the repository's root without a shell; `{python}` is the Python that runs
play.py. `model` names what answers, for the record. `timeout_s` (1–600) and `max_output_bytes` (1 KiB – 4 MiB) are
limits; past either, the command is killed. A configuration that is not exactly this is refused whole
(`STUDIO-CONFIG`), and play.py serves the world without a director.

## The request (on the provider's standard input)

`VERDANDI-STUDIO-REQUEST 1`, one JSON document (version 1 since STUDIO-1: `target`, `references`, `relations`, `mentions`
and `coordinates` in place of version 0's `selection`; version 2 since MARK-0, when the prompt names shapes: version 1
and `shapes`):

| field | |
|---|---|
| `id` | the request's id; the response must name it |
| `brief`, `head`, `base` | the brief, and the head the request was made at (the director's head and its three parts) |
| `prompt` | the designer's words, 1–2,000 characters |
| `target` | null, or the target's reference (as in `references`) |
| `references` | the target and the pins, each: its tag and role, whether the prompt mentions it, its id, address, kind, region and material; the brief's statement that made it (line, text, key), how many objects that statement makes, and what a revision of it can change; the address patterns it falls under (`plaza/canopy/*`, `material/concrete_slab`); its geometry (bounds, centre and size in metres, underside and top, long axis, orientation, its boxes and parts and lights, and the direction its lights point where the scene records one); the nearest wall of the play geometry (which, on which side, how far in plan and in space, its top); and its binding (the scene and head it was bound at, and whether it has changed since) |
| `relations` | for every two references: the gap between their boxes, whether they touch, their overlap in plan, the direction and distance from one centre to the other, the differences of their undersides and tops, whether they share a kind, a material, a statement, each marked *measured*; and, where the first records a facing, whether it faces the second, marked *inferred* (a half-space test on centres, not a line of sight, not a connection) |
| `mentions` | the tags the prompt names |
| `coordinates` | metres; x east, z south, y up; yaw 0 north; the cell's size and the walls' height; a box's six numbers |
| `camera` | where the designer stands and looks: x, y, z (metres), yaw and pitch (degrees) |
| `statements` | the brief: every statement's line, text and key |
| `revision_syntax`, `language` | how a revision is written, and the art file's statements as `art/README.md` describes them |
| `respond` | the response's format, the id again, at most 3 candidates, and the JSON Schema they follow |
| `shapes` | version 2 only (MARK-0): the shapes the prompt names, each: its name, operation and what it means, whether it is closed; the box and face it is on (the piece, its address, kind and layer, the statement that made it and what a revision of it can change, or the play geometry's, which the art cannot change); the face's size, origin, u and v; its vertices in the face's frame and in the world (metres); its area; the host's checks; the designer's words (unchecked) and note |

## The response (on its standard output)

`VERDANDI-STUDIO-RESPONSE 0`: `{"format", "version": "0", "id", "provider": {"name", "model"[, "usage"][, "stop_reason"]}, "candidates": [...][, "outcome": {...}]}`,
at most three candidates, each with exactly these fields (`python art/studio.py schema` prints the schema, which a
provider that supports constrained output should constrain its model to):

| field | |
|---|---|
| `title` | a few words, at most 80 characters |
| `rationale` | what the change means, at most 1,200 characters |
| `revision` | 1–16 lines: `= <statement>` replaces the statement with the same key, `+ <statement>` adds one, `- <key>` removes one |
| `scope` | 1–12 address patterns: everything outside them must stay as it is |
| `preserve` | what it means to keep, in words, at most 12 (recorded, and shown; the scope check is what holds it) |

`usage`, if a provider gives it, is exactly `{"input_tokens", "output_tokens", "cost_usd", "cost_basis"}`: two counts,
a cost in dollars or `null`, and a few words saying where the cost comes from (Claude Code's own client-side estimate;
the API's token counts with no cost, since prices are not a provider's to know). It is recorded, never charged against
anything here.

An exit status other than 0 is a failure; the last line of the provider's standard error is shown.

**Every request ends in a disposition (0220).** His first queued prompt, to add a figure, came back *"the director
proposed nothing"*, with no reason: the art file says canopies, towers, neon, lamps, puddles, materials, the sky and
the air, and nothing of people, vehicles or props, and the studio could not say so. Now the request publishes
`capabilities`: what the studio can make (`look.material`, `dressing.canopy`, ...) and, by name, the closed list of
what it cannot make yet (`entity.person`, `entity.vehicle`, `motion.path`, `motion.surface`, `mechanism.door`,
`physics.dynamic`, `audio`, ...). The response may carry `outcome`, the model's account when it proposes nothing:
`{"kind": none | unsupported | ambiguous | declined, "unmet": [names from that list], "questions": [...], "reason":
content | rights | safety | other, "note": "..."}`. The gateway decides, the host's observations first:

| disposition | when | decided by |
|---|---|---|
| `REALIZED` | one to three candidates came back (each then has its verdict: CLEAN, LEAKAGE, REFUSED) | the studio |
| `DECLINED` | the provider's API reported a refusal (`stop_reason` refusal, which the adapter passes on) | the studio |
| `UNSUPPORTED` | no candidates, and the outcome names what is needed from the list of what the studio cannot make | the provider (its account) |
| `AMBIGUOUS` | no candidates, and one to three questions for the designer, shown as text and never carried out | the provider |
| `DECLINED` | no candidates, and the provider declines with a reason from the closed list | the provider |
| `FAILED` | the provider could not be run or read (`STUDIO-*`), or it answered nothing and gave no reason (`STUDIO-EMPTY-WITHOUT-REASON`) | the studio |

An outcome that names a capability the studio has, or one the request never listed, refuses the response
(`STUDIO-RESPONSE-OUTCOME`). `INFEASIBLE` and `PROJECTED` are reserved for a repair stage that is not built. No
disposition but `REALIZED` evaluates, draws or writes anything: the brief and its ledger stay byte for byte as they
were. The scripted provider gives `UNSUPPORTED` when a word of the prompt is in its small list (a person, a vehicle, a
door, ...): word matching, not understanding. Whether Claude Code's CLI passes the API's stop reason on is not
measured; if it does not, a refusal on that path reads as `FAILED` or as the model's own account.

## What the gateway does with it

The response is read whole or refused whole. Each candidate becomes a `VERDANDI-INTENT` (art/director/intent.py):
the gateway gives it its letter (A, B, C), the base it was asked at and the designer's prompt; the provider gives the
rest. The director evaluates each at the current head (the art checks, and the scope check). A candidate it refuses is
shown with the reason and never drawn; one it finds CLEAN or LEAKAGE is compiled and served as a source the page can
switch to. Only a CLEAN candidate is admitted from the page, and only after it is evaluated again at the head as the
files stand and that head is the one it was drawn at.

| code | when |
|---|---|
| `STUDIO-CONFIG` | the configuration is not exactly as above |
| `STUDIO-NO-PROVIDER` | no director is configured |
| `STUDIO-PROMPT`, `STUDIO-SELECTION` | an empty or too long prompt; a piece the head's scene does not hold |
| `STUDIO-REFERENCE`, `STUDIO-PINS` | a prompt naming a tag that is not the target or a pin; a tagged object not in the scene at the head; the target pinned; an unpin of what is not pinned; a fifth pin |
| `STUDIO-PROVIDER-START` | the command cannot be started |
| `STUDIO-TIMEOUT`, `STUDIO-RESPONSE-SIZE` | past its time; past its output limit (killed) |
| `STUDIO-CANCELLED`, `STUDIO-SUPERSEDED` | cancelled by the designer; a newer request asked (killed, its result discarded) |
| `STUDIO-PROVIDER-EXIT` | it exited with an error (its last line of standard error shown) |
| `STUDIO-RESPONSE-JSON`, `-FORMAT`, `-ID`, `-FIELD`, `-CANDIDATES`, `-REVISION`, `-SCOPE` | the response is not JSON, not this format, for another request, or a field breaks its rule |
| `INTENT-*`, the director's verdicts | a candidate that is not an intent, or that the director refuses (`INTENT-APPLY`, `CHECK-FAILED`, …) or finds leaking (`LEAKAGE`) |
| `STUDIO-STALE`, `STUDIO-NOT-ADMISSIBLE`, `STUDIO-DECIDED`, `STUDIO-NO-CANDIDATE` | at admission: the head moved since it was drawn; not CLEAN; already decided; no such candidate |
| `STUDIO-NO-STILL`, `STUDIO-STILL-FLAGGED` | at admission (ADMISSION-0, 0222): no still taken of the candidate as drawn; a still the detectors flag, admitted only with "Admit despite" |
| `STUDIO-DIRECTOR-REFUSED` | the director itself refused the admission, refusal or undo (its own reason shown, and since 0245 its own code as `director_code`: `LEDGER-UNLOGGED`, `HEAD-MOVED`, …) |
| `STUDIO-ROUTE` | a studio route with no branch (0245) |
| `STUDIO-NOTHING-TO-UNDO`, `STUDIO-NOT-UNDOABLE` | no admission left to undo (an undo is never itself undone; undo again walks further back); one that changed the layout, or whose inverse is not CLEAN |

## The record and the still (ADMISSION-0, 0222)

Each candidate's card shows what the studio computed of it: its rung and why (from what changed, never from the
model's words), what an admission needs, and, folded, what was not checked. **Admit** draws the candidate if another
source is shown, waits two frames, takes the canvas as a PNG (a copy at most 960 pixels wide) and gives it to play.py
(`POST /studio/still`, the studio's token, the PNG as the body), which keeps it and reads its detectors (QUALITY-0) from
the bytes. With no flag the candidate is admitted with that still; with a flag nothing is admitted, the flag is shown,
and **Admit despite** appears beside it (recorded in the ledger). The still goes into the world's ledger folder by its
sha256 and `verify` reads it again. Undo needs no still: it is checked to be the exact inverse of the admission it
undoes. The detectors flag a still drawn white or black; they prove nothing about a picture, and the designer judges it.

## What is kept

Each line of `requests.jsonl` now carries its disposition and `prev`, the sha256 of the line before it:
`python art/studio.py records [--brief B] [--root DIR]` reads the record back, says whether the chain is whole (a line
taken out of the middle is found; lines cut from the end are not, without the last line's hash kept elsewhere), counts
the dispositions, and lists what was asked for and is not made yet, the studio's backlog (telemetry, never a gate).

Every request, under `art/build/studio/BRIEF/ID/` (never committed; in the studio's worlds, under the world's own
folder): `request.json`, `response.raw`, and each
candidate's intent (`A.intent`, …); and one line a request, admission, rejection or undo in
`art/build/studio/BRIEF/requests.jsonl`: the head, the configuration and the model it names, the prompt, the
target's address and every tag's object, the sha256 of the request and the response, and, as the owner asked (*"Record the provider, model, exit
status, schema-validation result and latency, without logging secrets"*), the provider and model the response names,
the exit status, whether the response was valid, the provider's time in milliseconds, the usage it reported, each
candidate's verdict and what it touched, and the outcome (a probe's requests are marked `"origin": "probe"`). Nothing a provider is given
or gives holds a credential, and none is recorded. play.py also prints one line a request (`STUDIO  ID  provider
(model)  time  tokens  A CLEAN; B LEAKAGE …`, or its refusal). A recorded candidate is played again without
the provider: `python art/play.py BRIEF --intent art/build/studio/BRIEF/ID/A.intent`. Admissions, rejections and undos
are in the brief's ledger (`art/ledger/BRIEF.ledger`), as `art/director.py` writes it.

## Its boundary

A provider is a command with an argument list, never a shell line; the request reaches it on its standard input, never
in its arguments. It is limited in time and in output, and killed when cancelled or superseded, with everything it
started: it runs in a process group of its own (POSIX), or is ended with `taskkill /T` (Windows), so that a model's own
command line cannot outlive a cancellation. play.py, stopping, does the same to a request running.

`claude_code.py` runs `claude` from an empty temporary folder with `--tools ""`, `--disallowedTools "mcp__*"`,
`--strict-mcp-config`, `--safe-mode`, `--no-session-persistence` and `--permission-mode dontAsk`, its own system text
(`--system-prompt-file`), the gateway's schema (`--json-schema`) and `--output-format stream-json`, so that the
session's first event, which lists the tools it offers, is read before its answer. If it offers any tool but
`StructuredOutput` (the means by which it holds its answer to the schema), claude is stopped and nothing it said is
used. Measured in the build container (Claude Code 2.1.296): `--tools ""` alone left a connected MCP server's 22 tools
offered; with `--disallowedTools "mcp__*"` the session offered `StructuredOutput` alone. The gateway reads its answer
again, whole, as it reads every provider's: the CLI's own enforcement of the schema is not relied on.

A provider's keys are in its environment; nothing of it reaches the browser but the candidates' text and their
verdicts, and the name, model and usage its response gives. The page's requests to play.py carry a token the page is
served with, in a header that a page of another origin cannot send without a preflight play.py never answers, and
every request, a GET too, must name 127.0.0.1 or localhost as its host: a page of another site that rebinds its own name
to 127.0.0.1 (DNS rebinding) is answered 403, so it reads neither the page's token nor the world, the prompts or the
queue. Nothing is admitted without the designer, and nothing reaches the
world but what the director judged.

**HARDEN-0 (0232): the boundary is total.** After ADVERSARY-A's 54 attacks on it (beside 0230 and 0231), every request
ends in an answer and every request a page starts ends: a Content-Length that is not a whole number of bytes (negative,
`abc`) is a 400, never read to the end of the connection; JSON nested too deep for the parser is a 400; a world named by
anything but a string, or a task's id that is not a string, is refused with its code (409) instead of a reset
connection; whatever a handler raises that it did not expect is answered 500 `STUDIO-INTERNAL` with the exception's
kind, its traceback on the console; a connection that stays silent is let go after a minute (`SOCKET_TIMEOUT`); a
prompt holding half of a character (a lone surrogate, as half an emoji pasted) is refused before it runs
(`STUDIO-PROMPT`), and a request's thread that raises anything ends the request failed (`STUDIO-FAILED`), recorded:
before 0232 that prompt left the request running for ever and the server busy. A camera that is not an object, or one
of 10^400 metres, is no camera. Since 0249 the server's listen backlog is 128, not Python's default of 5: on Windows a
connection that finds the backlog full is refused (after about 2 s), not queued, and a page asks for its scripts at once.
`python art/play.py --boundary-selftest` holds it (BOUNDARY SELFTEST 9/9: a burst of 32 connections to a server accepting
none all queued, and its plant, a backlog of 5, caught).

## Crash safety, and what a supervisor reads (B1)

Every admission is written so that a process killed at any point leaves the brief and its ledger at the parent or
the child, never between: `art/director.py`'s docstring says how, and `python art/director.py crashtest` kills an
admission at each of its writes and recovers it (15 cases since 0222, which added the point after an admission's still is kept). Every director command, and play.py's start, recovers
first. One writer at a time: every writer of a tree's ledgers, briefs, tags and maps holds the tree's content lock
(`art/build/content.lock`; a thread lock in a process and the system's lock between processes, which the system releases
when its holder dies); an admission holds it from before its first write to after its last and reads the head again
under it, so a second admission drawn at the same head is refused (HEAD-MOVED) instead of writing over the first; and
recovery takes the same lock, so while an admission is alive a recovery refuses (LEDGER-BUSY) and changes nothing.
`python art/director.py racetest` (32 cases) puts a second admission and another process's recovery at each of an
admission's writes, and keeps the plants that break it. Briefs share the graybox's maps, so a layout admitted in one
world would change every world that plays its map: a layout change is refused while another brief plays the map
(SHARED-MAP), an art change admitted as before. That holds in one tree; in the studio's worlds (STUDIO-2, below) each
world keeps a copy of the maps of its own. play.py answers `GET /healthz` (`ready`, `version`, `page`, `page_age_s`, `bye_age_s`, `pid`), takes the page's
heartbeat on `POST /studio/alive` (every 5 s) and its goodbye on `POST /studio/bye` (a `pagehide` beacon whose body is
the token, since a beacon cannot set a header), and stops on `POST /studio/shutdown`, SIGTERM or Ctrl+Break; it exits
0 stopped, 70 when its port is taken (bound exclusively on Windows), 75 when recovery refuses.

## The desktop studio (B1)

```
python art\studio_app.py shortcut --director art\providers\claude_code.json    once: a desktop icon, "Verdandi Studio"
```

The icon starts `pythonw art\studio_app.py`, the supervisor: it joins a job object of its own (so play.py, the
provider and the browser end with it), starts play.py on a free port without a console, opens Edge in application mode
with a profile of its own, and stops everything when the window is closed (the page's goodbye, not followed within 3 s
by its speaking again, as a reload does), when the page has not spoken for three minutes and no request is running (a
silent page is not a closed window: Edge's sleeping tabs freeze a background page's timers; while a provider works,
the studio waits for it, then stops), or when play.py ends. A second click opens another window on the same studio. Errors are shown in a dialog and kept in
`%LOCALAPPDATA%\VerdandiStudio\state\logs\`. `shortcut` keeps the shell's non-secret variables for the icon
(`VERDANDI_CLAUDE`, `VERDANDI_DIRECTOR_MODEL`, `VERDANDI_DIRECTOR_API`); a key never: for the API provider,
`ANTHROPIC_API_KEY` must be a user environment variable. Claude Code's native install
(`%USERPROFILE%\.local\bin\claude.exe`) is found without any. `python art/studio_app.py selftest` holds the lifecycle
with a stand-in browser (12 cases; 13 on Windows, where a live job's process list is read as well).

## The worlds and the queue (STUDIO-2)

The milestone, in the owner's words: *"Build a desktop-launched application that can open two saved worlds, switch
between them, queue an edit for either world, and review the resulting candidate without interrupting play."* Where
the worlds live is his choice of 2026-10-13: *"Per-user folder (Recommended)"*.

**Where.** `%LOCALAPPDATA%\VerdandiStudio\worlds\NAME\` (elsewhere `~/.local/share/verdandi-studio/worlds/NAME/`),
or `--worlds DIR`. Each world is a tree of its own: its brief (`art/briefs/NAME.art`), its ledger and tags
(`art/ledger/`), its own copy of the graybox's maps (`graybox/maps/`), its requests' records (`art/build/studio/`) and
its content lock (`art/build/content.lock`). One world's admission therefore writes no file of another, by
construction, and two worlds never share a map. The desktop studio serves this folder; `--root DIR` (one tree, the
self-tests') and the checkout itself are served as before.

**The first start.** When the folder holds no world it is made from the checkout: every brief there (four
today: `foundry-yard`, `harbor-day`, `harbor-lift` and `plaza-night`) is copied whole, with its ledger and tags if it has them and the checkout's maps, into a
folder made aside; its ledger is replayed in the copy, and only if it verifies is the folder put in place, by one
rename. A brief whose ledger does not verify is not copied, and why is said and recorded. `SEEDED.json` records what was
copied, by sha256. The checkout is read, never written (but for its own recovery, as any start there does); after the
first start it is a template, and the studio's worlds change only through their own ledgers.

**In the page.** The panel (**Enter**) names the world played and lists the others: choosing one loads its page.
**Duplicate as** makes a new world from this one (its brief, its title marked as a copy, a ledger of its own and, in the
worlds folder, its own copy of the maps) and opens it. The **Queue** section queues the prompt for any world, with a
provider (`art/providers/*.json`) and a model (or the configuration's own), and with that world's present target and
pins: the task runs in the background, and the page, and every world, plays on. A request asked with **Ctrl+Enter** is
the page's own, as before; a queued one is not tied to the window.

**The queue** (`art/studio_queue.py`). A task belongs to a world: it records the world, the references and the camera
it was queued with, the head when it was queued and when it ran, the provider's configuration and the model. Tasks run
in the order they were queued, at most two at once (`--jobs N`) and at most one per world, so that a world's requests
meet the head the one before left. A task is *queued*, *running*, then *ready* (its candidates recorded), *failed* or
*cancelled*; *interrupted* if the studio stopped while it ran and nothing of its answer was recorded; *reviewed* once
decided. The dock's **Queue** tab (the director's panel until 0249) lists every task with its state, its world and
prompt, its model, and the tokens or cost its provider reported, with **Cancel**, **Review**, **Set aside** and **Queue
again** as the state allows; a toast says when
one is ready or failed, in whatever world's page is open. **Review** opens the task's world (another world's page loads,
with `&review=ID`) and draws the task's recorded candidates again at the head as it is now, each evaluated again, never
trusted: a candidate made against an older head says so (`HEAD-MOVED` in its codes) and is admitted, as every
candidate is, only at the head it is drawn at. Nothing in the queue admits; the person does, through the gateway.

**Kept across restarts.** The queue is one file, `queue.jsonl` in the worlds folder, one event a line, each appended
under the queue's lock and flushed. Two rules from the ghost search (fixes 3 and 4 of 2026-10-13): a torn last line is
set aside (`queue.jsonl.torn.N`) and cut from the file, durably, before anything is appended, so the next event never
merges into it; and a task that was running when the studio stopped is *ready* if its world's records hold its answer
(nothing is asked, or paid for, again), *interrupted* otherwise, and can be queued again.

`python art/studio_queue.py selftest` (19 cases) seeds a worlds folder, refuses a brief whose ledger does not verify,
queues for one world from another's page and reviews and admits there (the other world's ledger unchanged), duplicates
a world, runs two worlds at once with one request per world, cancels and queues again, compiles two worlds' scenes at
once (and keeps the plant without the export lock), and keeps fixes 3 and 4 with their plants. The studio app's
self-test starts the supervisor without `--root` on a worlds folder.

## The first window (0220)

By his direction of 2026-10-13, *"when i click the desktop icon a window should open asking what part of the studio
should open first; different abstractions can be added as be design"*: the icon's window opens on `start.html`, which
lists the worlds, each read back as the window opens (its ledger replayed to its files, under its content lock: VERIFIED
says the files are the bytes the ledger records, not that the world is right; whether the head is anchored outside the
world folder is said, and it is not yet), and the studio's views, one manifest each in `art/web/views/`:

| view | level | what |
|---|---|---|
| Play and direct | make | the world first-person with the director's panel |
| Queue prompts | make | the same, with the queue open |
| Compose | make | not built: a top-down blockout; says why |
| History | one level deeper | the ledger and the request record read back, read-only, with the head and the last line's hash to copy elsewhere |
| Mechanisms | one level deeper | not built: arrives with the first physics slice; says why |
| Evidence | one level deeper | not built: the self-tests' results; says why |

A view is added by adding a manifest (`id`, `title`, `summary`, `level`, `order`, `open`, `needs_world`,
`capability` inspect or propose, `status` ready or not built, `why`); one that is not well formed, or that opens a page
outside the studio, is listed as unavailable with why, never left out. The window and the read-only views are served
with a second token, good for the window's heartbeat and goodbye and nothing else: they cannot ask, admit, reject,
undo or queue. *Next time, skip this window* is a preference of the window's own browser profile, never part of a
world. `python art/studio_queue.py selftest` holds the launcher (the token, a broken manifest, a world changed outside
its ledger not verified) and `python art/studio_app.py selftest` the window opening on it.

## What is not shown

The quality of what a model proposes: the checks hold a candidate to the rules of the art and to its declared scope,
not to taste. The live Anthropic API: `anthropic_messages.py` is held only to a local server that answers as the API's
documentation describes. `claude_code.py` has been run against the real CLI in the build container (Linux) and on the
owner's Windows machine (`claude.exe` from Claude Code's own installer, his Claude plan, 2026-10-12), its probes SHOWN
in both; a `.cmd` or `.ps1` shim is refused, not measured beyond the self-test's. That a model
identifies the intended objects in general: the references' probe is four prompts about three canopies, a few runs,
one model. A tag on a light or a play piece (E and R pick the dressing's boxes; a light goes with its object). Tags
shared between two pages at once. The structured-outputs request against the live API (no key here). An image of the view (the next slice, by his sequence) and
pieces that connect two objects (after it). A scope pattern that names one object with its parts: the director's
grammar has none, so a model told only an object's exact address declares a scope that leaves its ribs and lights
out (`SCOPE-LEAK`); the request now says so. Changes to the layout (the look only; a layout change is the design
tool's). A long-running worker: each request starts the provider's command afresh, which the owner allowed for the
first version. A latency in general: the scripted provider answers in well under a second, and Claude Code's CLI took
9–17 s a request in the build container's probes, which says nothing of another machine, model or prompt.
STUDIO-2: switching worlds in a browser on a real GPU (in the build container's headless Chromium, on SwiftShader, a
page with a live WebGL context took 40 to more than 90 s to give way to the next, the server having answered in about a
millisecond; the browser run gave the context back first, and passed its ten flows); whether a provider started by the
desktop studio opens a console window (it is started with `CREATE_NO_WINDOW`; not seen on Windows yet); a studio that
dies between asking a provider and recording that the task started finds the task still queued at its next start,
and asks again (the first answer, if one came, is in the world's records, but not the task's).
