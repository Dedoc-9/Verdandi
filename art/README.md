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

The reach ceiling of a cell is the highest standable top among the cell and its eight neighbours, plus the body
(1.80 m, an assumption of this layer: the graybox player has no head), the jump's apex (1.225 m: a jump of 7 m/s
under 20 m/s²) and a margin of 0.25 m. A cell is standable when a player can get onto it from a spawn, each step
climbing at most the jump's apex. So a 1 m crate is standable and a 2.6 m pillar is not. Decoration that should change
play is not art: it goes into the graybox map as cover and is checked there (the owner's three-worlds rule,
[`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md)).

Each dressing choice is a hash of its statement and its cell, never a running random sequence. An edit in one place
cannot reshuffle the art anywhere else.

## The art file: `VERDANDI-ART 0`

One statement to a line; `#` starts a comment. Colours are R,G,B 0–255 (sRGB), lengths metres, cells `x,z` (x across,
z down). [`briefs/plaza-night.art`](briefs/plaza-night.art) is the first.

| statement | meaning |
|---|---|
| `map NAME` | the graybox map to dress (required, once) |
| `title TEXT` · `seed WORD` | a name; the word every choice is hashed with |
| `time night\|dusk\|day` · `moon AZ EL LUX R,G,B` (or `sun`) | the sky; the one directional light, from azimuth AZ (0 north, 90 east) and elevation EL |
| `fog DENSITY R,G,B [volumetric]` · `exposure EV` · `bloom N` · `rain 0..1` | the air and the camera |
| `asset NAME PATH SOURCE LICENCE…` | a mesh, its engine path, its source (`engine`, `cc0`, `fab`, `generated`, `own`) and its licence; a mesh without both is refused |
| `material NAME R,G,B ROUGH METAL [emissive R,G,B STRENGTH]` | a surface |
| `surface CLASS MATERIAL` | the play geometry's look: `ground`, `floor`, `stair`, `raised`, `cover`, `wall` |
| `region NAME x0,z0 x1,z1` | a named place the look talks about |
| `skyline MATERIAL MIN MAX` | 2 × 2-cell blocks of rock that border no floor, raised to MIN–MAX m |
| `tower REGION MATERIAL MIN MAX` | the rock cells bordering a region's floor, raised to MIN–MAX m |
| `canopy REGION MATERIAL HEIGHT [x0,z0 x1,z1]` | an overhead slab, which must clear the reach ceiling |
| `neon REGION MATERIAL HEIGHT EVERY` | a flush strip and a rect light on one in EVERY of the region's rock faces |
| `lamp REGION R,G,B CANDELAS SPACING` | a point light and its housing over floor cells on an absolute lattice |
| `puddle REGION MATERIAL PERCENT` | flat black-water planes on that share of the region's floor cells |
| `view NAME x,z YAW PITCH` | a first-person viewpoint for critique, on a standable cell |

**A look revision** (`VERDANDI-ART-REVISION 0`, [`briefs/plaza-night.revise-look`](briefs/plaza-night.revise-look))
replaces the brief's statements of the same verb and name and nothing else. **A layout revision**
([`briefs/plaza-night.revise-layout.design`](briefs/plaza-night.revise-layout.design)) is design text, admitted through
the design tool after the layout's own design. Its `# region` line says where its cells may change.

## Run it

```
python art/dress.py plaza-night          # art/build/plaza-night/: scene.json, lineage.json, plan.svg (a top view, not a render)
python art/check.py                      # every brief: ends ART CHECKS PASSED
```

`art/check.py` exports each brief twice (the bytes must agree), then holds the scene to the world it dresses:

- the graybox map's own checks pass;
- the collision boxes, laid back onto the grid, are C cell for cell;
- no dressing stands where a player can be;
- no piece has collision; the player is the one `graybox/web/sim.js` declares and the spawns are W's; the reach
  ceiling is the one recomputed independently;
- every mesh names its source and licence;
- the lineage's hashes are the files' own.

It then plants defects and requires the right check to refuse each one:

- a wall's box dropped, or a cover box made taller;
- a decorative wall on open floor;
- a canopy under the reach ceiling, or a sign standing off its wall;
- dressing given collision;
- a falsified ceiling, a player who jumps lower than `graybox/web/sim.js` says, or a spawn moved from W's;
- a mesh with no licence;
- a scene changed after export;
- five statements the exporter must refuse.

Then it makes the two revisions:

- **The look revision** may change only the materials it names, and does.
- **The layout revision** is compiled and admitted through the design tool. Play must still hold, and every piece of the scene that changed must stand within a cell of a changed cell. A collision box may change anywhere in an 8 × 8 chunk holding a changed cell.

The layout revision needs the shell (`rustc` or a built `verify/build/shell`). Without it the line says SKIPPED, and
the verdict says so too.

## In Unreal Engine 5.8, on the host

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
| `briefs/plaza-night.art` | the first brief: a rain-soaked brutalist coastal plaza at night, on the tactical graybox |
| `briefs/plaza-night.revise-look` | its look revision: the wet surfaces less reflective |
| `briefs/plaza-night.revise-layout.design` | its layout revision: the north flank one cell narrower |
| `unreal/verdandi_import.py` | the Unreal 5.8 importer, run inside the editor |
| `build/` | what `dress.py` writes; never committed |
