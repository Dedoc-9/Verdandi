# graybox/ — FPS-GRAYBOX-0, the playable slice

A first-person graybox you can launch, walk, jump and shoot in, built on the studio's canonical level. It is a
runtime beside the certified tree, not part of it: nothing here is a row of the gate, and nothing here writes
into `kernel/`, `shell/`, `workshop/`, `verify/`, `oracle/` or `design/`.

```text
  tactical.design ──design tool──► shell design-compile ──► shell design (admit) ──► tactical.layout   walls and floor
                                                                                          │
  tactical.gbx  (height, cover, spawns, objective, targets, probes, routes) ──────────────┤
                                                                                          ▼
                                                level.py:  D ──► W canonical world ──► C collision world
                                                                       │                   │
                                                      render.js (draws W)          sim.js (moves against C)
```

## Run it

Python 3 (standard library only) and a browser with WebGL. From the repository's root:

```
python graybox/serve.py
```

It converts the map, serves the game on `127.0.0.1` and opens it in your default browser. `python graybox/serve.py
witness` plays the oracle's witness level as it stands. Add `--no-browser` to print the address only, `--port N` to
choose the port. Ctrl+C in the terminal stops it.

**Controls.** Click the view to capture the mouse. WASD (or the arrows) move, the mouse looks, Space jumps, the
left button fires, R returns you to your spawn, 1 and 2 respawn at base A or base B, M shows or hides the map, Esc
releases the mouse.

## Test it

| what changed | run |
|---|---|
| map content (`maps/`) | `python graybox/check.py` — the conversion's conformance and its mutations; add `--compile` to compile and admit the tactical layout again through the design tool (needs a built shell, as the design tool does) |
| the runtime (`web/`) | `python graybox/serve.py tactical --selftest` — opens the page in self-test mode, prints every check and ends 0 if all passed |
| the certified tree | the gate, at a release checkpoint |

`check.py` reads the source again with its own reader and holds the canonical world W and the collision world C to
it: walls and floor as the source says, collision as the canonical world says, provenance on every cell, spawns on
open floor, probes that block or stay open, the routes and the bases connected. Then it plants six defects the
conversion could have (an opening collapsed by the converter or in the source, a spawn in a wall, an invisible
blocker, a wall made passable, provenance stripped) and a seventh through the converter itself, and requires each to
be refused. It writes each map's manifest to `graybox/build/` (not committed).

The self-test runs inside the page, against the runtime's own collision and movement: load; both spawns; every probe
walked at; each route walked end to end by a bot through the real movement; gravity and the jump; a 1 m cover block
refused on foot and mounted with a jump; a hit in the open, a miss behind a wall, the target back up; reset; a
recorded route replayed twice with the state hashed at every tick; and one frame drawn.

## The files

| | |
|---|---|
| `maps/tactical.design` | the tactical map's walls and floor, in the design language (`VERDANDI-DESIGN 0`) |
| `maps/tactical.layout` | what the shell's compiler and admission made of it, read back through the design tool, with the design's sha256 and the session heads |
| `maps/tactical.gbx` | the overlay: cell size, wall height, heights, cover, spawns, objective, targets, probes, routes |
| `maps/witness.gbx` | the overlay on the oracle's witness level, read from its bytes and pinned by their sha256 |
| `level.py` | the converter: D to W and C, and the manifest |
| `check.py` | the map checks, for map content |
| `serve.py` | the launcher and the self-test's driver |
| `web/sim.js` | the simulation: movement, collision, gravity, the weapon, the targets, the self-test. No DOM; runs under node too |
| `web/render.js` | the renderer: WebGL 1, one shader, graybox colours and a 1 m grid |
| `web/main.js`, `web/index.html` | input, the fixed-tick loop, the HUD, the map, self-test mode |

## The map format, `GRAYBOX 0`

One statement to a line, `#` to the end of a line is a comment. Cells are `x,z`, x across and z down from 0; a
rectangle is two corners.

```
GRAYBOX 0
name tactical
layout tactical.layout            # or: level oracle/levels/witness.lvl <sha256>
cell 2                            # metres a cell
wall 4                            # the walls' height
spawn A 3,15 90                   # side, cell, yaw in degrees: 0 north (-z), 90 east (+x)
objective 22,14 25,17
height 22,13 25,18 1.0            # raise floor cells (platforms, steps)
cover 12,14 12,14 1.0             # a solid block on floor cells, its top in metres
target 10,16
probe wall 1,15                   # must block;  probe open 23,8 — must stay open
route north 3,15 6,4 41,4 44,16   # waypoints the checks walk
```

The overlay adds to floor and never moves a wall: a statement on a rock cell of the layout is refused with its line.
The design language has no height, collision volume or gameplay mark. Those live here, and the language is not
stretched to say them.

## What runs, and what does not

Runs: a 3D first-person scene with walls, floors, openings, steps, a raised platform and cover; mouse look and WASD;
collision against the collision world and the standing targets; gravity and a jump that mounts 1 m cover; one weapon
(hitscan, a 0.12 s cooldown) with a placeholder model, a muzzle flash, a hit marker and target feedback; six targets
that drop when hit and stand again after 2.5 s; reset and respawn at either base; an objective zone; a mini-map; the
page's own software timings (frame, simulation, draw submission, input to tick).

Not here: other players, damage to the player, an objective that scores, ammunition and reload, sound, ramps (heights
step by at most 0.55 m), ceilings, overhangs and anything not a column standing on a cell. Interpolation between
ticks. The timings are software timestamps inside the page: they stop at the browser's hand-off to the compositor
and are not input-to-photon. Determinism is claimed for one build in one browser: the replay check compares two runs
in the same page. Nothing is claimed across browsers or machines.

## Boundaries

See [`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md). In short: the simulation moves against the collision world and
reads no render data; the renderer reads the state and writes none of it; input reaches the simulation only as a
tick's input record.
