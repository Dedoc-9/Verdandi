<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# art/ — prompted art over a playable world (ART-GENERATION-0)

The owner's pivot (2026-10-10): *"the verification should exist only to guarantee the purity of the art. we want to
move from verification to enabling the user to prompt art through llm and i mean at the quality of aaa games."* His
finite decision: *"Unreal; curated modular assets + CC0 + selective AI props; separate `graybox/` project. Keep
verification subordinate to artistic intent and gameplay integrity."* This folder is that project. It is named `art/`
because `graybox/` is the browser slice it dresses. It stands beside the certified tree, as the graybox does: no row
of the gate reads it, and it changes nothing the gate holds.

## The loop

```text
  a prompt ──► the art file (the look: palette, materials, massing, light, air, views)       a model writes it
           ──► the layout (walls and floor) through the design tool: propose, preview, admit  the owner admits it
  graybox/level.py: the layout + the map's overlay ──► W (canonical) and C (collision)
  art/dress.py:     W, C + the art file ──► one scene (scene.json), its lineage, a plan view
  art/check.py:     the scene held to C and the player; planted defects refused; two revisions
  art/quality.py:   the scene's bytes exact (finite, one byte form, known and bounded, in budget); frozen references; detectors on stills
  Unreal 5.8:       art/unreal/verdandi_import.py ──► the level: play geometry, dressing, light, air, views
  play ──► critique in plain words ──► a look revision (the art file) or a layout revision (the design tool) ──► again
```

The model proposes; it never writes the world. A look is an art file, which the checks hold before anything reaches
the engine. A layout change goes through the design tool's own preview and admission, like any other. Visual quality
is judged by a person from rendered viewpoints: no check here certifies that the art is good, only that it cannot lie
about play.

## Four worlds, one rule

| world | what it says | who writes it |
|---|---|---|
| W, canonical | walls, floor, heights, cover, spawns, the objective, probes, routes | the admitted layout and the graybox map |
| C, collision | every cell's solid top: where a player can stand and what blocks | derived from W by `graybox/level.py`; nothing else |
| A, the art file | the look: materials, massing, canopies, neon, lamps, puddles, air, viewpoints | a model or a person |
| S, the scene | C as play geometry in the look's materials, the dressing, the lights | `art/dress.py`, from W, C and A |

**The rule.** The scene's collision is C, exactly, and nothing the art adds has collision or stands where a player can
be. Every piece of dressing is one of:

- **inside rock**: over cells whose top is the wall's (towers, the skyline);
- **inside or flat on a solid top**: no higher than the cell's top plus 2 cm (puddles, decals; a skin inside a cover
  block);
- **flush on a rock face**: at most 8 cm deep against a rock neighbour (signs, neon strips);
- **above every head**: wholly above the cell's reach ceiling (canopies, lamp housings).

**The reach ceiling, REACH-1 (0229).** Every scene is played under the graybox's rules 3
([`graybox/RULES-3.md`](../graybox/RULES-3.md)), and says so (`rules`): a cell as high as the wall holds a body at any
height, so nobody stands on the rock and dressing inside it is out of every head's way; a target has a top a player
can stand on. Over that world the ceiling of a cell is the highest a head can rise over it, plus a margin of 0.25 m:

- **where a body may stand**: every open cell's top; every mover's top, over its whole travel in plan, from its lowest
  to its highest; every target's top, over its column (its radius, 0.4 m, either way of its centre);
- **which of them are reached**: from the spawns' cells, a body reaches a surface s2 from a surface s when, jumping
  from s's highest (7 m/s up, 20 m/s² down, 6 m/s across), its feet are still as high as s2's lowest less the step
  (0.55 m; less nothing for a target, which holds a body below its top) after flying the gap between the two, less a
  radius (0.35 m) at each end: with `need = lo2 − allowance − hi`, `need ≤ apex` (1.225 m) and
  `gap ≤ 2·radius + speed·t`, `t = (jump + √(jump² − 2·gravity·need)) / gravity`. Nothing between them is asked to be
  open, which can only add surfaces;
- **the head over a cell**: from each reached surface, the body flies the gap to the cell less two radii at the
  walking speed; while it rises (0.35 s) its head is at the surface's highest plus the apex plus the body (1.80 m, an
  assumption of this layer: the graybox player has no head), after that falling, and a fall below 0 is not counted
  (the body lands first, on a surface counted itself). An open cell no surface reaches keeps its own top plus the body,
  the apex and the margin; a rock cell none reaches has no ceiling.

The arithmetic is written once and done the same way in the exporter and in `art/check.py` (square roots by
`math.sqrt`, correctly rounded on every machine, never `**` or `pow`), so the two ceilings are the same numbers.
Before 0229 a climb was the apex alone and only to a neighbouring cell: the simulation climbs the apex and a step
(1.775 m), crosses gaps and stands on targets, and the old ceiling sat 2.3 m under a head beside a 2.6 m cover
(MEASURED, 0229: in a search of rules 3's simulation over the tactical map, 334 cells where a head rose above the old
ceiling less its margin; none above REACH-1's, the closest 0.029 m under it). Decoration that should change play is
not art: it goes into the graybox map as cover and is checked there (the owner's three-worlds rule,
[`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md)).

Each dressing choice is a hash of its statement and its cell, never a running random sequence. An edit in one place
cannot reshuffle the art anywhere else.

**One fixture to a place.** A place is a kind of dressing and the cell (and face) it stands on. Two pieces in one
place, from overlapping regions or two statements, are coplanar copies that flicker in an engine, and the exporter
refuses them. The first brief had two puddles in one place where its mid lane crossed the plaza; the mid lane is now
two regions, west and east.

## The art file: `VERDANDI-ART 0`

One statement to a line; `#` starts a comment. Colours are R,G,B 0–255 (sRGB), lengths metres, cells `x,z` (x across,
z down). [`briefs/plaza-night.art`](briefs/plaza-night.art) is the first. **A number** (0226) is ASCII digits, at most
one `.` with digits on both sides, and a `-` in front when negative: `7`, `0.82`, `-10`. Nothing else is read as one
(`+2.5`, `2_5`, `25e-1`, `.5`, `5.` and digits of other scripts are refused, which Python's `float()` alone took); a
spacing, a percentage or an `every` is a whole number (`3` or `3.0`, never `2.7`).

| statement | meaning |
|---|---|
| `map NAME` | the graybox map to dress (required, once) |
| `title TEXT` · `seed WORD` | a name; the word every choice is hashed with |
| `time night\|dusk\|day` · `moon AZ EL LUX R,G,B` (or `sun`) | the sky; the one directional light, from azimuth AZ (0 north, 90 east) and elevation EL. The native renderer reads LUX on a linear scale of its own, set on the night plaza's moon (0.35) and with no exposure of its own: a midday sun there is about 2.5 (`harbor-day`); a real sun's 100,000 lux, as Unreal takes it, is drawn white |
| `fog DENSITY R,G,B [volumetric]` · `exposure EV` · `bloom N` · `rain 0..1` | the air and the camera |
| `asset NAME PATH SOURCE LICENCE…` | a mesh, its engine path, its source (`engine`, `cc0`, `fab`, `generated`, `own`) and its licence; a mesh without both is refused |
| `material NAME R,G,B ROUGH METAL [emissive R,G,B STRENGTH]` | a surface |
| `surface CLASS MATERIAL` | the play geometry's look: `ground`, `floor`, `stair`, `raised`, `cover`, `wall` |
| `region NAME x0,z0 x1,z1` | a named place the look talks about |
| `skyline MATERIAL MIN MAX` | 2 × 2-cell blocks of rock that border no floor, raised to MIN–MAX m |
| `tower REGION MATERIAL MIN MAX [mass]` | the rock cells bordering a region's floor, raised to MIN–MAX m: one prism a cell, or with `mass` a few masses (each run of cells one block, cut into at most five segments stepped 2 m from MAX at the middle of each side to MIN at the ends, each with a cornice above every head) |
| `canopy REGION MATERIAL HEIGHT [x0,z0 x1,z1] [deep D] [ribs N] [lit R,G,B CANDELAS] [edgelit R,G,B CANDELAS]` | an overhead slab, which must clear the reach ceiling: D m deep (0.4 if not given), with downstand ribs 0.8 m deep every N cells across it, downlights set into its underside every other cell along it, and a narrow row of small fixtures, one a metre, along the edge that faces the region's middle. The ribs and the lights must clear the reach ceiling too |
| `neon REGION MATERIAL HEIGHT EVERY` | a flush strip and a rect light on one in EVERY of the region's rock faces |
| `lamp REGION R,G,B CANDELAS SPACING` | a point light and its housing over floor cells on an absolute lattice |
| `puddle REGION MATERIAL PERCENT` | flat black-water planes on that share of the region's floor cells |
| `view NAME x,z YAW PITCH` | a first-person viewpoint for critique, on a standable cell |
| `mover NAME MATERIAL X0,Y0,Z0 X1,Y1,Z1 along AXIS travel METRES speed M/S [policy stop\|push]` | (0226) a box that goes out `travel` metres along AXIS (`+x`, `-x`, `+y`, `-y`, `+z`, `-z`) and back, again and again, at `speed` metres a second; it carries a player who stands on it ([`graybox/RULES-2.md`](../graybox/RULES-2.md)). Its policy (0229, [`graybox/RULES-3.md`](../graybox/RULES-3.md)) says what it does with a player in its way: `stop` (the default) holds it still; `push`, along x or z only, moves the player with it and holds it still only when the player cannot go (a push along y is refused: say stop). Its corners and travel are whole numbers of 1/256 m below 1,024 m, and its speed a whole number of 1/256 m a tick (a multiple of 0.46875 m/s; 0 parks it). Refused when the rules refuse it (the tunnelling bound), or when its travel leaves the world, meets a cell's solid, crosses a spawn's or a target's column, another mover's travel or a piece of dressing (a piece flat on the floor may lie under it). Every scene names rules 3 and is played under them. **A person's edit only:** a mover is play, and the director refuses any intent that adds, removes or moves one (SCOPE-PLAY), whatever it grants; a mover's material is its look (`surface/mover`) |

**A look revision** (`VERDANDI-ART-REVISION 0`, [`briefs/plaza-night.revise-look`](briefs/plaza-night.revise-look))
replaces the brief's statements of the same verb and name and nothing else. **A layout revision**
([`briefs/plaza-night.revise-layout.design`](briefs/plaza-night.revise-layout.design)) is design text, admitted through
the design tool after the layout's own design. Its `# region` line says where its cells may change.

## Run it

```
python art/dress.py plaza-night          # art/build/plaza-night/: scene.json, lineage.json, plan.svg (a top view, not a render)
python art/check.py                      # every brief: ends ART CHECKS PASSED
python art/preview.py plaza-night        # art/build/plaza-night/preview.html: a first-person sketch to open in a browser
```

**The preview is PROVISIONAL_PREVIEW.** It shows the scene's boxes in their materials' colours, the moon, every lamp
and neon as a point light, and fog, from the brief's views (keys 1–9) or walking. It is a sketch for judging
composition and height between admissions, before Unreal is installed. It is not the Unreal look, it decides nothing,
and nothing hashes its pixels.

`art/check.py` exports each brief twice (the bytes must agree), then holds the scene to the world it dresses:

- the graybox map's own checks pass;
- the collision boxes, laid back onto the grid, are C cell for cell;
- no dressing stands where a player can be;
- no piece has collision; the player is the one `graybox/web/sim.js` declares and the spawns and targets are W's; the
  reach ceiling is the one recomputed independently (REACH-1);
- the rules: the scene names rules 3, which `graybox/web/sim.js` and `graybox/tick_ref.py` both say they implement
  (the handshake, read from their sources); each mover inside the rules' table, its policy stop or push (push along x
  or z), its travel in the world and clear of the spawns', the targets' and the other movers' columns;
- every mesh names its source and licence;
- the lineage's hashes are the files' own;
- the scene's bytes are exact (QUALITY-0, `art/quality.py`): finite JSON in the exporter's one byte form, with no NaN,
  no Infinity and no number that overflows to one, no key twice, no integer above 2^53 − 1; every field known, with its
  type and range (a field the checker does not know is refused, not passed over); every box with extent, inside the
  world, and every coordinate under 1,024 m, where the renderer's float32 keeps the scene's 0.1 mm steps apart; inside
  the native renderer's budgets, read from its own source (160 lights, after which it drops the rest without a word;
  2,048 cells, the visibility texture's width WebGL 2 guarantees, as recalled from OpenGL ES 3.0 and not re-read), and
  two chosen budgets (4,096 boxes, 4 MiB);
- the scene is its frozen reference (`art/references.jsonl`): the same art at the same exporter gives the same bytes on
  every machine. When the exporter changes, this line fails, naming the fields the new exporter moved, until a person
  freezes the new references (`python art/quality.py freeze NAME --note TEXT`, appended; the old lines are kept).

It then plants defects and requires the right check to refuse each one:

- a wall's box dropped, or a cover box made taller;
- a decorative wall on open floor;
- a canopy under the reach ceiling, or a sign standing off its wall; a slab at 4.5 m beside the 2.6 m cover, clear of
  the ceiling before 0229 and not of a head on the cover (and the same slab at 6.0 m, which passes);
- a scene that names rules 2, rules 4 or none; a lift that pushes; a target moved from W's;
- dressing given collision;
- a falsified ceiling, a player who jumps lower than `graybox/web/sim.js` says, or a spawn moved from W's;
- a mesh with no licence;
- a scene changed after export;
- six statements the exporter must refuse, among them two pieces of dressing in one place.

Then it makes the two revisions:

- **The look revision** may change only the materials it names, and does.
- **The layout revision** is compiled and admitted through the design tool. Play must still hold, and every piece of the scene that changed must stand within a cell of a changed cell. A collision box may change anywhere in an 8 × 8 chunk holding a changed cell.

The layout revision needs the shell (`rustc` or a built `verify/build/shell`). Without it the line says SKIPPED, and
the verdict says so too. It also says SKIPPED when the admitted layout already holds the revision. That happened when
candidate B of the first round was admitted (2026-10-10), because B closed the same three cells of the north flank.
The revision now narrows the south flank instead, so the check has a change to test again.

## DIRECTOR-0: prompts answered by candidates, admitted by a person

[`director/README.md`](director/README.md) is the protocol. A prompt is answered by candidate intents: each declares
what it will touch, and changes the look (art lines), the layout (design lines, through the design tool) or both.

```
python art/director.py lens plaza-night plaza            # what a proposer reads: the region, its pieces, what shares their materials
python art/director.py evaluate plaza-night art/rounds/plaza-imposing/*.intent   # verdicts and a contact sheet
python art/director.py admit plaza-night SEQ            # a person's choice, by ledger number
python art/director.py verify plaza-night                # the ledger replayed to the files
python art/director.py selftest                          # the vectors and the whole lifecycle, in a scratch copy
python art/director.py crashtest                         # an admission killed at each of its writes, then recovered
python art/director.py racetest                          # writers at once: the content lock, the fence, recovery that waits
```

- **Each candidate is checked against the head it meets.** It gets one of three verdicts: CLEAN; LEAKAGE (it touches
  more than it declared, including everything that shares a material it changed); or REFUSED (a reserved or
  ungranted change, a failed art check, a malformed or unknown intent).
- **The contact sheet** (`art/build/<brief>/director/index.html`) draws each candidate's plan, with what changed,
  what was affected and what leaked.
- **The ledger** (`art/ledger/<brief>.ledger`) keeps every evaluation, re-evaluation, admission and refusal, and is
  never rewritten.
- **The first round** is `art/rounds/plaza-imposing/`. Two more wait on the owner's choice: `art/rounds/plaza-mass/`
  ("make the towers read as one monumental mass, not a comb") and `art/rounds/plaza-cantilevers/` ("make the
  cantilevers more imposing"), both evaluated at the head after the exporter's rebase (ledger #14); the second's D
  and E, written for the owner's art note, at the head after the next (#21).

## The native plaza: `art/play.py`

By the owner's ruling (2026-10-10): *"Make Verðandi-native the primary architecture. Keep UE5.8 as a secondary
interoperability path."* And (2026-10-11): *"Choose the art-owned launcher (`art/play.py`) and WebGL2 in the browser.
Keep `serve.py` and the existing `graybox/` boundary unchanged."*

```
python art/play.py plaza-night           # compiles the scene, holds it to the art checks, serves it; a browser opens
python art/play.py plaza-night --intent art/rounds/plaza-cantilevers/D.intent --intent art/rounds/plaza-cantilevers/E.intent
                                         # the brief, and each candidate as the director evaluates it; [ and ] step through them
python art/play.py --selftest            # the live loop without a browser: LIVE SELFTEST 18/18
```

- **The launch.** It compiles the brief through `dress.py` and runs the art checks on the scene. A scene that fails
  one is not served. It serves, on 127.0.0.1 only, these paths and no other: the page and the renderer
  (`art/web/`), the graybox's `sim.js` (read and served unchanged), the scene from memory, and the map converted by
  `graybox/level.py`. The browser gets no other path into `art/` or `graybox/`, and nothing is written to disk.
- **Who decides what.** The simulation moves the player against the map's C and nothing else. The renderer
  (`art/web/scene_render.js`, WebGL 2) draws the scene and writes no state.
- **What it draws.** The moon's shadow; every lamp, neon and downlight, each seen only from the cells it can see
  across the grid; surfaces patterned by what they are; light thrown up from the lit floor onto undersides; the sky
  dimmed by the masses around; height fog and each lamp's glow in it; the wet floor and the puddles as mirrors; rain
  and its rings; bloom.
- **In the page.** Click to play (W A S D, the mouse, Space, R). Keys 1–9 move a camera to the brief's views and Tab
  goes back to play. `--art PATH` plays another art file for the same brief (a candidate's text). `--intent FILE`
  (any number) adds a source: the brief with that intent applied, as `director.py` evaluates it at the current head
  (its verdict is shown; a REFUSED candidate is not served; nothing is written to the ledger). `[` and `]` step
  through the sources without leaving the game.
- **Live edits.** Unless `--no-watch`, play.py watches every file the sources are made from (the art file, the
  intents, the graybox's maps, and the code under `art/` and `graybox/` that compiles them). When one's bytes change,
  it compiles the sources that depend on it again, in a fresh Python process (so an edit to `dress.py` is used too),
  holds them to the same checks, and serves what passes; what does not pass leaves the scene before it served, and
  the page says why. The page asks `/live` twice a second. A new scene on the same map is drawn in place, its bytes
  held to the digest `/live` gave, and the game is not touched: the same state, the same world, the same snapshot. A
  new map is a new collision world, so a new game at the spawn: the edit is new authority, nothing of the old game is
  carried into it. A new `scene_render.js` takes the canvas over from the old one, or, if it does not start, the old
  one goes on drawing; a new `play.js` or `sim.js` is announced, and the page's reload loads it. This is the loop for
  an edit a model writes: it writes the intent (or the art file), and the running world shows it, or says why not.
- **The limits.** Nothing hashes its pixels; a person judges what it draws. It is the first native renderer, not AAA:
  boxes with procedural surfaces, no global illumination, no textures, and no shadows from the point lights.
- **The studio (STUDIO-0, STUDIO-1).** With `--director CONFIG.json`, E makes the object under the crosshair the
  target, R pins one as a reference (each tagged object named and framed on screen as `@1`, `@2`, …), and Enter
  summons a director: the prompt, the tags and the camera go to `studio.py`'s gateway, which asks the configured
  provider (a command; `providers/scripted.json` needs no model, `providers/claude_code.json` asks Claude through
  Claude Code's CLI on its own login, `providers/anthropic.json` through the Messages API with a Console key) for at
  most three candidates, has the director evaluate each, and serves those it does not refuse as sources the page
  switches to in place, each with what it touches. Admit, Reject and Undo go through the ledger. The contract is in
  [`STUDIO.md`](STUDIO.md); `python art/studio.py selftest` holds the gateway (STUDIO SELFTEST 61/61), `probe` asks a
  real model whether it answers and follows the prompt (`--references`: whether it changes the objects the prompt
  names, and only those), and `report` compares the providers from what was recorded.
- **The worlds and the queue (STUDIO-2).** The desktop studio serves the worlds in a per-user folder
  (`%LOCALAPPDATA%\VerdandiStudio\worlds\`, made from the checkout's briefs the first time), each a tree of its own
  with its own ledger and maps; `play.py NAME --worlds DIR` serves them. The page switches between worlds, duplicates
  one, and queues a prompt for any world while it plays on (`studio_queue.py`); a ready task is reviewed in its own
  world's page, its candidates drawn again at the head as it is then. `python art/studio_queue.py selftest` holds it
  (STUDIO-2 SELFTEST 19/19); [`STUDIO.md`](STUDIO.md) says how.
- **The shell (STUDIO-3, 0230).** The play page is a studio around the play surface, after the owner's mockup: a menu
  bar, the scene, layer and selection, a navigator, the viewport with its tools, pills and measured statistics, an
  inspector (`/object.json`, read from the scene served; nothing bound), the layers and the world's settings, an asset
  browser with thumbnails a second renderer draws, the candidates, the ledger, and the roadmap. It opens in an editor
  (a click selects what the ray through the cursor meets; P plays, Esc returns). Nothing in it is the world: it reads
  what `play.py` serves and asks `play.py` to act. What is not built says so. [`STUDIO.md`](STUDIO.md), *The shell*.
- **Every request ends in a disposition; the icon opens a first window (0220).** A request that comes back without
  candidates says why: UNSUPPORTED (with what the studio cannot make yet, from a closed list the request publishes),
  AMBIGUOUS (the director's questions), DECLINED (the API's refusal, or the provider's), or FAILED (including an
  empty answer with no reason); none of them writes the world, and the request record is hash-chained
  (`python art/studio.py records`). The desktop icon's window asks what to open first: the worlds, each read back,
  and the views, one manifest each in `web/views/`.

## In Unreal Engine 5.8, on the host (an optional path)

Since the owner's ruling of 2026-10-10, Unreal is a secondary interoperability path, not the critical one.

First, the smallest end-to-end scene on the machine you will build on, before any kit or toolchain is bought:

1. Install Unreal Engine 5.8 from the Epic Games Launcher.
2. Create a project: Games → **First Person**, Blueprint, Desktop, Maximum quality. Starter content is optional. Name
   it `VerdandiArt` and put it in this folder (`art\unreal\`). Git ignores `art/unreal/*/`: the project's inputs are
   here, and the project itself is made from them.
3. Edit → Plugins: enable **Python Editor Script Plugin**, then restart the editor.
4. File → New Level → **Empty Level**, and save it (for example `/Game/Verdandi/L_PlazaNight`).
5. Run `python art/dress.py plaza-night` in the repository.
6. In the editor's Output Log, set the box at the bottom to **Cmd** and enter, with your own paths:
   `py "C:/…/Verdandi/art/unreal/verdandi_import.py" "C:/…/Verdandi/art/build/plaza-night/scene.json"`
7. Press **Play**. The spawn is base A's. The cameras under *Verdandi/Views* are the critique viewpoints: select one,
   right-click → Pilot, then `HighResShot 1920x1080` in the Cmd box for a still.

The importer makes everything in one editor transaction (Ctrl+Z undoes it). It tags every actor with its scene id, so
a second run on a revised scene keeps every unchanged actor and remakes only what changed. It then checks the level
against the scene in the engine: the collision actors must lay back onto C, and no dressing may have collision. It
writes `unreal-report.txt` beside the scene, and that report is the evidence of the host run.

It also reports the template character's movement against the graybox player the checks assume: walk 600 cm/s, jump
700 cm/s, gravity scale 2.04 (20 m/s²), step 55 cm. Where they differ, set them in the character Blueprint's Character
Movement. Otherwise the reach ceiling the checks compute is not the one you play.

## What is shown, and what is not

| claim | grade | where |
|---|---|---|
| the scene's collision is C; no dressing where a player can be; the revisions stay local; each planted defect refused | MEASURED, here | `python art/check.py` (the build container, 2026-10-10) |
| the importer's logic: a first import, a second that keeps every actor, a look revision that remakes none, a layout revision that remakes 5 and removes 4, the in-engine self-check passing | OBSERVED against a stand-in for the `unreal` module, not an engine | the build container; the stand-in is not in the repository |
| the importer runs in Unreal 5.8 | NOT_MEASURED | the host's first run; its report |
| the scene's bytes are exact: finite, one byte form, every field known and bounded, inside the native renderer's budgets; each brief its frozen reference | MEASURED, here | `python art/quality.py selftest` (58 rows, each check against its planted defect) and `python art/check.py` (the build container, 2026-10-13) |
| the reach ceiling (REACH-1) is above every head the graybox's rules 3 raise | MEASURED, here, as a search and not a proof: a breadth-first search of rules 3's simulation over landings (24 yaws, jumps at once, after 3 or 8 ticks, or none; with movers, after waiting 0, 60 or 150 ticks), every tick's head over the cells under the body: the tactical map, 308,352 tries, no head above REACH-1's ceiling less its margin, the closest 0.029 m under it, 334 cells above the old one; harbor-lift with its movers, 400,032 tries, none above, the closest 0.029 m | the build container (node v22), 2026-10-14; the search is not in the repository |
| the detectors on stills (white, black, a channel at 255, distinct colours) flag a still drawn white and not a sound one | OBSERVED on 21 stills of the two briefs, chosen with them in view; a detector, not a proof; its miss and false-alarm rates NOT_MEASURED | `python art/quality.py still FILE.png` |
| the scene looks good | NOT_MEASURED, and no check can measure it | rendered viewpoints, judged by a person |

The first scene uses only the engine's cube: concrete masses, wet floors, black puddles, neon, sodium lamps, moonlight
and volumetric fog. It is the hardware test, not the look. The kit comes next, and so do CC0 textures, selected AI props
and rain particles (a Niagara system is an asset). Each asset is declared with its source and licence, and placed
under the same rule. A prop sits inside a cover block, on rock, flush on a wall or above every head. A prop meant to
block a player is cover, and goes into the graybox map.

## Files

| file | what |
|---|---|
| `dress.py` | the exporter: the art file and the graybox world to one scene, its lineage and a plan view |
| `check.py` | the art's checks, plants and revisions |
| `preview.py` | the provisional first-person preview (PROVISIONAL_PREVIEW): a standalone WebGL 2 page of the scene |
| `play.py` | the native plaza's launcher: the sources (the brief, candidate intents) compiled, checked and served beside the graybox's simulation, and compiled again when their files change; the studio's endpoints; its own self-test and the studio's |
| `web/studio_ui.js` | STUDIO-3: the shell's icons (inline SVG), its DOM builder, the view's arithmetic (a camera's basis, a point projected, the ray through a pixel, where a ray enters a box and through which face, MARK-0's face frames) and the thumbnailer (a second renderer on a small canvas) |
| `studio_refs.py` | STUDIO-1: what a tagged object is, its geometry in metres, its nearest wall, and how two stand (measured from the scene's boxes; a facing marked inferred) |
| `director/durable.py` | B1: the content path's writes made to survive a killed process (an append flushed; a file replaced whole by a flushed temporary and a write-through rename); the death points `art/director.py crashtest` kills at; the content lock every writer of a tree's ledgers, briefs, tags and maps holds (a thread lock and the system's file lock, released by the system when its holder dies), which `art/director.py racetest` holds to account |
| `studio_app.py` | B1: the desktop studio's supervisor (a job that ends everything it starts, play.py without a console, Edge in application mode, stopping when the window closes) and its `shortcut`; `selftest` with a stand-in browser. STUDIO-2: it serves the worlds folder (`--worlds DIR`, the per-user folder by default) |
| `studio_queue.py` | STUDIO-2: the queue of creative work — prompts queued for any world with a provider and a model, run in the background at most one per world, kept across restarts in `queue.jsonl` (a torn last line set aside and cut; a task whose answer was recorded ready, not lost); `selftest` seeds worlds, queues, reviews, duplicates and keeps its plants |
| `fixtures/round/` | 0229: the round the director's self-tests play, `rounds/plaza-imposing/`'s candidates over its base with its two slabs at 6.0 m, which REACH-1 clears (its README says why; the owner's round is unchanged) |
| `fixtures/selftest/` | the self-tests' world: the plaza's brief and layout as committed when the self-tests were written, laid under a scratch root by `director.py`'s `selftest_tree`; the self-tests never read the working brief, ledger or tags, which are the owner's world |
| `studio_txn.py` | the studio's change transaction as a reference (docs/STUDIO-CONTRACT.md): the promotion journal's form and grammar and `Recover(J, P, F)`; `check` holds it over every enumerated crash point, `selftest` plants wrong decisions, `recover ROOT` reads a studio and prints what its stub must do; nothing here launches or writes a studio |
| `studio.py`, `STUDIO.md` | STUDIO-0: the director gateway (a provider's request and response, its limits and refusals, the candidates evaluated, admitted, rejected and undone through the ledger; `probe` and `report`), and its contract |
| `providers/` | the gateway's providers: `scripted.py` (fixed variations of a selected canopy, not a model), `claude_code.py` (Claude through Claude Code's CLI, `claude -p`, on its own login; tools off, no session kept) and `anthropic_messages.py` (Claude through the Anthropic Messages API on structured outputs, its key in the environment, its model the configuration's, `claude-opus-5-5`), each with its configuration; `director_prompt.py`, what both model providers tell their models |
| `web/start.html`, `web/start.js`, `web/views/` | 0220: the studio's first window: the worlds read back, the views from their manifests (a view is added by adding one); it holds a token good only for its heartbeat |
| `web/history.html`, `web/history.js` | 0220: the History view, read-only: a world's ledger and request record read back, with the head and the last line's hash to keep elsewhere |
| `web/play.html`, `web/play.js` | the native plaza's page: input, the fixed tick on `sim.js`, the views, the live swap, the studio's tags (E target, R pin, the names and frames on screen) and panel |
| `web/scene_render.js` | the native renderer (WebGL 2); `load(S)` draws another scene in place, `dispose()` frees it |
| `briefs/plaza-night.art` | the first brief: a rain-soaked brutalist coastal plaza at night, on the tactical graybox |
| `briefs/harbor-day.art` | STUDIO-2's second world: sunlit harbour terraces at midday, on the same graybox, nothing of the layout moved |
| `briefs/harbor-lift.art` | 0226: harbor-day with a deck sliding along the south lane and a lift beside the tall block at its west end, the first world with movers; 0229, the deck pushes a player in its way |
| `briefs/plaza-night.revise-look` | its look revision: the wet surfaces less reflective |
| `briefs/plaza-night.revise-layout.design` | its layout revision: the south flank one cell narrower (the north flank until B was admitted) |
| `unreal/verdandi_import.py` | the Unreal 5.8 importer, run inside the editor |
| `director.py`, `director/` | DIRECTOR-0: the canonical form, the scope protocol, the ledger, the conformance vectors, the second implementation |
| `rounds/plaza-mass/`, `rounds/plaza-cantilevers/` | the second and third rounds, evaluated, not yet chosen |
| `rounds/plaza-imposing/` | the first round's candidate intents |
| `ledger/plaza-night.ledger` | the brief's intent ledger |
| `build/` | what `dress.py` writes; never committed |
