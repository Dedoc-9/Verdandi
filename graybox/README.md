# graybox/ — FPS-GRAYBOX-0, the playable slice

A first-person graybox you can launch, walk, jump and shoot in, built on the studio's canonical level, and since
FPS-VISUAL-0 lit and dressed. It is a runtime beside the certified tree, not part of it: nothing here is a row of the
gate, and nothing here writes into `kernel/`, `shell/`, `workshop/`, `verify/`, `oracle/` or `design/`.

```text
  tactical.design ──design tool──► shell design-compile ──► shell design (admit) ──► tactical.layout   walls and floor
                                                                                          │
  tactical.gbx  (height, cover, spawns, objective, targets, probes, routes) ──────────────┤
                                                                                          ▼
                                                level.py:  D ──► W canonical world ──► C collision world
                                                                       │                   │
                                                      render.js (draws W)          sim.js (moves against C)
                                                      decorates, decides nothing that blocks
```

## Run it

Python 3 (standard library only) and a browser with WebGL. From the repository's root:

```
python graybox/serve.py
```

It converts the map, serves the game on `127.0.0.1` and opens it in your default browser. `python graybox/serve.py
witness` plays the oracle's witness level as it stands. Add `--no-browser` to print the address only, `--port N` to
choose the port, `--renderer flat` to play with the graybox's first renderer, `--timeout S` to bound a self-test's
or bench's wait. Name the map before any option: the parser takes the first word that is not an option's value, so
`serve.py --port 8000 witness` plays the tactical map. Every map is converted at launch, so a refused map stops any
launch. Ctrl+C in the terminal stops it.

**Controls.** Click anywhere on the page to capture the mouse. WASD (or the arrows) move, the mouse looks, Space
jumps, the left button fires, R returns you to your spawn, 1 and 2 respawn at base A or base B, M shows or hides the
map, G shows or hides the 1 m grid (the lit renderer; the first renderer always draws it; `?grid=1` starts with it),
Esc releases the mouse.

## Test it

| what changed | run |
|---|---|
| map content (`maps/`) | `python graybox/check.py` — the conversion's conformance and its mutations; add `--compile` to compile and admit the tactical layout again through the design tool (needs a built shell, or `rustc` to build one, as the design tool does) |
| the runtime (`web/`) | `python graybox/serve.py tactical --selftest` — opens the page in self-test mode, prints every check (27 on the tactical map, 24 on the witness level) and the `MEASURED` lines, and ends 0 if every check passed |
| where two engines part (a diagnostic) | `python graybox/trace.py run tactical` — records and plays the self-test's walk and fight in a worker, logging every call of `Math.sin`, `Math.cos`, `Math.hypot` and `Math.atan2` with its arguments' and result's bits, every tick's input and snapshot, and the browser's description of itself; writes `graybox/build/trace/tactical/ENGINE.json` and `latest.json` (not committed). Then `python graybox/trace.py compare A.json B.json` for two such traces, and `python graybox/trace.py selftest A.json` for the comparator's own planted differences |
| the renderer's cost | `python graybox/serve.py tactical --bench` — both renderers draw the same poses in your browser, alternating; the timings print, and they and a screenshot of each pose by each renderer are written to `graybox/build/bench/tactical/` (not committed). A sample is the mean of a batch of draws, each followed by a one-pixel readback; the page's clock step is printed, since some browsers round it (to 1 ms). Add `--samples N` (default 20), `--batch K` (default 10) |
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
recorded route replayed twice with the state hashed at every tick. Then the renderers: each built and one frame
drawn; the state the same after frames by both (`render-readonly`); and `render-conforms`, which holds the lit
renderer's mesh to the collision world face by face (every top at its cell's height, every upright face from the lower
neighbour's height to its cell's, every step drawn, no other solid), keeps every decoration outside the map or above
the highest eye a player can reach (found by its own search, on the movement's numbers), and the target inside its
hit box. On the witness level, which has no 1 m cover, the cover check reports itself not applicable and counts as
passed.

The replay compares hashes, so four checks say what an equal hash is worth. Each runs on two runs made by playing
(the first route's recorded walk, and a fight: shots, a jump, a walk, the targets standing again, a change of side),
and each has a planted defect it must refuse:

- **`hash-coverage`.** The state's leaves are found by walking it, not listed by hand. Every leaf must be seen by the
  hash at its last bit, or be one the world declares (a target's name and place) that equals the world's value and
  that no tick writes. The last bit is one byte of the hash's input, and FNV-1a always tells apart two inputs that
  differ in one byte (each of its steps is a bijection), so a pass is not luck. Plants: a hash blind to the vertical
  velocity `vy`, one blind to the targets' `downFor`, an unhashed leaf written every tick, and an unhashed leaf the
  world does not declare.
- **`fx-noninterference`.** The view's feedback (`s.fx`: the hit marker, the flashes, the last shot) never reaches
  the authoritative state, which is why the hash may leave it out. At reachable states a twin with the feedback
  swapped is stepped beside the original, and the two must stay the same bit for bit at every following tick. Plant:
  a tick that reads the flashes.
- **`snapshot-resume`.** The authoritative state is everything a tick reads. Snapshots (every number written as its
  IEEE 754 bits) are read back exactly and resumed in fresh instances of the simulation, which share no variable with
  the one that took them, and every later tick must match. The rules (`P`) are frozen. Plant: a tick count kept
  outside the state.
- **`resume-realm`**, in the page. The walk is resumed in a worker (`web/sim_worker.js`), a JavaScript realm with its
  own globals and its own copy of `sim.js`, and every later tick must be this page's state bit for bit. A snapshot
  with one bit changed must come apart at the first tick, so the comparison is shown able to fail.

Together: the hash sees the whole authoritative state, what it leaves out cannot change that state, and that state
is all the next tick reads, in this instance, a fresh one or another realm. So equal replay hashes mean an equal game,
up to a 32-bit hash's collisions between states that differ in more than one byte. All of this is in one browser.

After the checks, the page prints lines marked `MEASURED`, which are measurements, not checks: nothing passes or
fails on them and they are not counted. Each run is played again in a worker whose `Math.sin`, `Math.cos` or
`Math.hypot` (the functions a tick calls whose results the language does not fix to the last bit) is off by its last
bit at every call: a counterfactual engine. The lines say from which tick the state's bits part from the page's, how
far apart the player ends, and whether any cell, footing or hit differs. In the build container, in Chromium and
again under node, the tactical walk's bits parted at tick 1172 of 1787 and ended 2.8 × 10⁻¹⁴ m apart, with no cell,
footing or hit different and the fight unchanged. A last-bit change in a small step is mostly absorbed when it is
added to a position near 50 m, but once one rounding goes the other way the bits stay apart, and the final hash
differs. (A real engine differs on some inputs, not on every call; this model is the harsher one.) On the owner's machine
every check matched the container's but four of the eight lines did not, so the two engines' `Math` differed
somewhere in these runs and rounding absorbed it (R-6 in [`docs/RESEARCH-FINDINGS.md`](../docs/RESEARCH-FINDINGS.md)).

The trace experiment (`trace.py`) is where that is pinned down. It is a diagnostic beside the self-test, not part of it,
and nothing passes or fails on what it finds. Its comparison takes each function's results only on the arguments
both runs passed, so that runs which have already parted, and so call a function with different arguments, are not
mistaken for a function that differs. In call order, it says whether the first difference is in an argument (the runs
had parted before that call) or in a result (the functions differ). For each run, it gives the first tick whose input
differs and the first tick whose state differs, with the leaves that differ there. A state that matches is only as
complete as the snapshot, which the self-test's `hash-coverage` and `snapshot-resume` hold to the whole of it. In the
build container, node 22 (V8 12.4) and Chromium 141 (V8 14.1) gave different results, one ulp apart, for `Math.sin`
on 5 of 745 arguments and `Math.cos` on 2 of 745 on the tactical map. `hypot` and `atan2` were the same. Every input
and every tick's state of both runs was the same. The owner's Firefox 157 against that Chromium (2026-10-11): `hypot`
different on 943 of 3,523 arguments and `sin` on 1 of 745, `cos` and `atan2` the same, each by one ulp, and again
every input and state the same at every tick. Observed once; what it does not show, and a remedy left to the owner,
are in R-6.

## The files

| | |
|---|---|
| `maps/tactical.design` | the tactical map's walls and floor, in the design language (`VERDANDI-DESIGN 0`) |
| `maps/tactical.layout` | what the shell's compiler and admission made of it, read back through the design tool, with the design's sha256 and the session heads |
| `maps/tactical.gbx` | the overlay: cell size, wall height, heights, cover, spawns, objective, targets, probes, routes |
| `maps/witness.gbx` | the overlay on the oracle's witness level, read from its bytes and pinned by their sha256 |
| `level.py` | the converter: D to W and C, and the manifest |
| `check.py` | the map checks, for map content |
| `serve.py` | the launcher, and the driver of the self-test and the bench |
| `trace.py` | the trace experiment: its own small launcher (four files and the map), and the comparison of two traces |
| `web/sim.js` | the simulation: movement, collision, gravity, the weapon, the targets, the state's snapshots, the self-test. No DOM; runs in a worker and under node too |
| `web/sim_worker.js` | the simulation in a realm of its own, for the self-test and the trace: resumes a snapshot, plays a run in a counterfactual engine, or records and plays the two runs with Math logged |
| `web/trace.html`, `web/trace.js` | the trace experiment's page |
| `web/render.js` | the renderer (FPS-VISUAL-0): WebGL 1; a sky, a sun whose shadow is traced through the heights, floor modules, panelled walls, dressed cover, beams on the wall tops, a skyline outside the map, the weapon in the hand; the 1 m grid on G |
| `web/render_flat.js` | the graybox's first renderer, kept unchanged but for its name: one shader, flat colours, the 1 m grid (`--renderer flat`) |
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
A probe may name rock. The converter also refuses a map without both spawns, a spawn or a target on cover, a height or
cover not between the floor and the wall's top, cover not above its floor, and an unknown statement. A rectangle may be
one corner.
The design language has no height, collision volume or gameplay mark. Those live here, and the language is not
stretched to say them.

## What runs, and what does not

Runs: a 3D first-person scene with walls, floors, openings, steps, a raised platform and cover; mouse look and WASD;
collision against the collision world and the standing targets; gravity and a jump that mounts 1 m cover; one weapon
(hitscan, a 0.12 s cooldown) drawn as a rifle with a kick, a sway and a muzzle flash, a hit marker and target
feedback; six targets (on the tactical map) that drop into the floor when hit and stand again after 2.5 s; reset and respawn at either base; an objective zone; a mini-map; the
page's own software timings (frame, simulation, draw submission, input to tick).

Not here: other players, damage to the player, an objective that scores, ammunition and reload, sound, ramps (heights
step by at most 0.55 m), ceilings, overhangs and anything not a column standing on a cell. Interpolation between
ticks. A shot aimed at an overhead beam passes through it: the beams are decoration. The timings are software
timestamps inside the page: they end inside the page's own callbacks (the draw time is its submission, not the
GPU's completion), before anything is composited, and are not input-to-photon. Determinism is claimed for one build in one browser: the replay check compares two runs
in the same page, and the state checks above say what its equal hashes cover. Nothing is claimed across browsers or
machines; the counterfactual lines measure how a last-bit difference would carry, in the browser they run in.

## Boundaries

See [`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md). In short: the simulation moves against the collision world and
reads no render data; the renderer reads the state and writes none of it, and decorates without deciding what blocks;
the weapon in the hand is drawn apart from the shot, which leaves from the eye; input reaches the simulation only as
a tick's input record.
