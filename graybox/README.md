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
| the runtime (`web/`) | `python graybox/serve.py tactical --selftest` — opens the page in self-test mode, prints every check (30 on the tactical map, 27 on the witness level) and the `MEASURED` lines, and ends 0 if every check passed |
| the rules' arithmetic (`web/sim.js`, rules 1) | `python graybox/rules_ref.py` — the same algorithms in Python: the digests and constants `sim.js` holds, the special values, the square root and hypot checked exactly, the source naming no engine function, three plants; and the accuracy, measured. Ends with `RULES REFERENCE PASSED` |
| the tick's second implementation (`tick_ref.py`, `RULES-1.md`) | `python graybox/tick_ref.py verify TRACE.json` — first the door (VERIFY-DOOR-0, 0255): the runs, their starts and their inputs must be the ones made here from the map (the walk, the fight, the stress run), each refusal a FAIL row with its own code (VERIFY-MAP to VERIFY-PLAY); then the trace played again in Python, from the specification, every tick's snapshot compared byte for byte; `python graybox/tick_ref.py selftest TRACE.json` — three plants in the trace (one at the door, run only on a trace of the browser's own runs, otherwise a SKIP that says why) and six in the Python tick, each found; `python graybox/tick_ref.py doortest TRACE.json` (a trace of the browser's own three runs) — the trace verified through the door; 27 attacks, each refused by its own code with every row before it passed; three plants in the door's reading of the fight; four inputs that once ended in a traceback; 25 bounds (a start far away or infinite, a value the readers take for a number and cannot read, a name or a userAgent that would print a line of its own), each judged in bounded time with nothing raised and every line legible; the three readers of a detail; and the harness plant, the door switched off (17 of the 27 VERIFIED again). Ends with `TICK REFERENCE VERIFIED`, `TICK-REF SELFTEST PASSED` and `DOOR SELFTEST 64/64` (on the witness map `63/64  (1 not run, said above)`) |
| ORT-1: the origin moved between ticks (`ORT-1.md`, `web/ort_cases.json`) | `python graybox/ort_ref.py` — the table played in Python (its own transform), each case held to the values worked by hand (the state after a rebase built from the state before and the worked numbers alone), every committed rebase held to conservation in exact fractions, twelve plants each refused by its own case; `python graybox/trace.py run tactical --ort --browser msedge` (or `firefox`) — the same table through `web/ort.js` in a browser, written to `graybox/build/trace/tactical/ort/`; then `python graybox/ort_ref.py graybox/build/trace/tactical/ort/chromium.json` — the browser held to the worked values and to Python, byte for byte, and five changes planted in its results, each found. Ends with `ORT-1 HELD BY PYTHON AND THE ENGINE` |
| rules 2: movers (`RULES-2.md`, `web/rules2_cases.json`) | `python graybox/tick_ref.py rules2` — rules 2's table played in Python, each case held to the values worked by hand from `RULES-2.md`, the case of no movers held to rules 1, and five plants in the Python tick that the worked values must catch; `python graybox/trace.py run tactical --rules2 --browser msedge` (or `firefox`) — the same table in a browser, written to `graybox/build/trace/tactical/rules2/`; then `python graybox/tick_ref.py rules2 graybox/build/trace/tactical/rules2/chromium.json` — the browser held to the worked values and to Python, every tick's snapshot and hash. Ends with `RULES 2 HELD BY PYTHON AND THE ENGINE` |
| rules 3: solid walls, targets with a top, push (`RULES-3.md`, `web/rules3_cases.json`) | `python graybox/tick_ref.py rules3` — rules 3's table played in Python, each case held to the values worked by hand from `RULES-3.md`, and where rules 3 change what rules 2 do, played under rules 2 as well and held to what the case says rules 2 do; nine plants in the Python tick that the worked values must catch; `python graybox/trace.py run tactical --rules3 --browser msedge` (or `firefox`) — the same table in a browser (and its rules-2 runs), written to `graybox/build/trace/tactical/rules3/`; then `python graybox/tick_ref.py rules3 graybox/build/trace/tactical/rules3/chromium.json`. Ends with `RULES 3 HELD BY PYTHON AND THE ENGINE` |
| the input contract (`RULES-1.md`, *The input*; `web/input_cases.json`) | `python graybox/tick_ref.py cases` — the shared table of hostile inputs played in Python, each step held to its required outcome (a tick, or a refusal with its category and the state unchanged), with four plants that must break it; `python graybox/trace.py run tactical --cases --browser msedge` (or `firefox`) — the same table played in a browser, written to `graybox/build/trace/tactical/cases/` (not committed); then `python graybox/tick_ref.py cases graybox/build/trace/tactical/cases/chromium.json` — the browser's results held to the table and to Python, step by step. Ends with `INPUT CONTRACT HELD BY PYTHON AND THE BROWSER`. The page's self-test plays the table too (`input-contract`) |
| the bot's walk (`bot_ref.py`, `WALK-1.md`) | `python graybox/bot_ref.py make tactical` — the walk made in Python from the map alone, written to `graybox/build/bot/tactical-walk.json` (not committed); `python graybox/bot_ref.py check FILE` — read whole or refused, made again the same, held to what a walk is for; `python graybox/bot_ref.py compare FILE TRACE.json` — beside a browser's walk, the start, each input and each state; `python graybox/bot_ref.py selftest TRACE.json` — made three times, and the plants. Ends with `BOT TRACE CHECKED`, `BOT TRACE AGREES WITH THE BROWSER'S WALK` and `BOT-REF SELFTEST PASSED`. `python graybox/trace.py run tactical --inputs graybox/build/bot/tactical-walk.json --browser msedge` has a browser play it |
| where two engines part (a diagnostic) | `python graybox/trace.py run tactical` — plays the self-test's three runs (the walk, the fight, the stress run) under rules 0 and under rules 1 in a worker, logging every call of `Math.sin`, `Math.cos`, `Math.hypot`, `Math.atan2` and `Math.sqrt` with its arguments' and result's bits, every tick's input and snapshot, and the browser's description of itself; writes `graybox/build/trace/tactical/ENGINE.json` and `latest.json` (not committed). `--inputs A.json` plays A's runs instead of recording its own, so that two browsers play the same inputs; `--browser msedge` (or `chrome`, `firefox`) opens the page in that browser and refuses a trace from any other engine family, so a file named `chromium-given.json` is a Chromium engine's; `--name LABEL` adds a file. Then `python graybox/trace.py compare A.json B.json` for two such traces, rules by rules, and `python graybox/trace.py selftest A.json` for the comparator's own planted differences |
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

The replay compares hashes, so four checks say what an equal hash is worth. Each runs on three runs made by playing
(the first route's recorded walk; a fight: shots, a jump, a walk, the targets standing again, a change of side; and a
stress run of 3,600 ticks made from integers alone: held moves of every kind, a turn and a look at every tick, jumps,
shots, a change of side, into walls and along them), and each has a planted defect it must refuse:

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

Two checks hold the rules' arithmetic, described in the next section: `rules-arithmetic` and `math-fence`.

After the checks, the page prints lines marked `MEASURED`, which are measurements, not checks: nothing passes or
fails on them and they are not counted. The first two: rules 0's replay of its own walk, against the baseline hash
recorded on 2026-10-10 (`91350c39A` on the tactical map, `ce819a52A` on the witness level), and this engine's own
`Math.sin`, `Math.cos`, `Math.atan2`, `Math.hypot` and `Math.sqrt` against the rules' functions over the same
arguments. Then each run is played again, under rules 0, in a worker whose `Math.sin`, `Math.cos` or `Math.hypot`
(the functions a rules-0 tick calls whose results the language does not fix to the last bit) is off by its last
bit at every call: a counterfactual engine. Last, rules 1 in a worker whose five functions are all off: the same
state at every tick, since rules 1 call none of them. The lines say from which tick the state's bits part from the page's, how
far apart the player ends, and whether any cell, footing or hit differs. In the build container, in Chromium and
again under node, the tactical walk's bits parted at tick 1172 of 1787 and ended 2.8 × 10⁻¹⁴ m apart, with no cell,
footing or hit different and the fight unchanged. A last-bit change in a small step is mostly absorbed when it is
added to a position near 50 m, but once one rounding goes the other way the bits stay apart, and the final hash
differs. (A real engine differs on some inputs, not on every call; this model is the harsher one.) On the owner's machine
every check matched the container's but four of the eight lines did not, so the two engines' `Math` differed
somewhere in these runs and rounding absorbed it (R-6 in [`docs/RESEARCH-FINDINGS.md`](../docs/RESEARCH-FINDINGS.md)).

## Rules 2: movers (0225)

[`RULES-2.md`](RULES-2.md): rules 1 with movers — boxes on one axis, ping-pong, in phase units of 1/256 m — that carry
a player standing on them (by the exact displacement, before anything else of the tick), stop rather than move into a
player, and are refused unless slow enough that no tick can pass one through a player (the tunnelling bound); a box
wholly above the head is a ceiling; a parked mover is a static box. Every rules-2 hash is FNV-1a 64 bound to an
identity: the rules' version, every constant (gravity and the timestep among them), the map and every mover. A world
without movers plays the same ticks under rules 2 as under rules 1. `GrayboxSim.withRules(2)`; `tick_ref.py`'s rules
2 are written from the same document. The native plaza (`art/play.py`) plays rules 2 for a scene with movers, which the
art language's `mover` statement makes (0226); `serve.py`'s pages play rules 1.

## The simulation's contract: rules 1

By the owner's ruling of 2026-10-11: *"investigate and implement the deterministic math layer now"*, *"Keep the scope
limited to authoritative state, and let the measured divergence—not a blanket desire for identical math—determine
which operations need replacement"*, and *"if the contract is cross-browser deterministic simulation, test state
transitions and serialized state—not just a handful of function outputs."*

**What must be the same, bit for bit, in every conforming JavaScript engine** (rules 1):

1. the world, `new World(map)`, from the map's canonical bytes;
2. the transition: `step(world, state, input)` gives the same next state, as its snapshot's bytes, on every input the
   input contract admits, and refuses every other input with the same category, the state unchanged
   ([`RULES-1.md`](RULES-1.md), *The input*; INPUT-CONTRACT-0; its table held in node 22, Chromium 141, Firefox 157
   and Edge 155, every outcome and state Python's);
3. the serialized state: `snapshot` and `restore` (every number as the 16 hex digits of its bits), and `hash`
   (FNV-1a over each number's bytes, little-endian, now written so whatever the platform's order). A NaN's bits are
   not fixed by the language, so a NaN in the state would break this. Before the input contract an infinite turn made
   one (the yaw NaN from then on); since it, no admitted input does, and NaN and the infinities are refused;
4. the inputs a run is made of: the bot's walk (`walk`), the fight's start (`makeRuns`), the stress run, each a
   function of the map alone;
5. the rules' arithmetic: `xsin`, `xcos`, `xatan2`, `xhypot` and `xsqrt` (`Sim.math`).

**What need not be:** the renderers (`render.js`, `render_flat.js`, `art/web/scene_render.js`), the view's feedback
`s.fx`, the HUD and the mini-map, timings, the `MEASURED` lines. A player's own input (a mouse's movement times the
sensitivity) is data: it is recorded as given, as bits, and replayed as recorded.

**Where the engine's functions reached the state** (rules 0, every call site in `sim.js`):

| call | where | what it decides | |
|---|---|---|---|
| `Math.sin`, `Math.cos` of the yaw | `step` | the direction a step walks | the transition |
| `Math.hypot(mx, mz)` | `step` | the step's length: the direction divided by it | the transition |
| `Math.cos`, `Math.sin` of the pitch and the yaw | `aim`, in `fire` | the shot's ray: a hit or a miss, the score, a target down | the transition |
| `Math.hypot`, `Math.atan2` | `walk`, the bot | when a waypoint is reached; the turn it inputs | the inputs |
| `Math.hypot`, `Math.atan2` | `lines`, `makeRuns` | which cell the fight starts from; its yaw and pitch | the start |
| `Math.atan2`, `Math.hypot` | the self-test's probes, cover and weapon | a walker's or shooter's yaw and pitch; a distance | the checks' runs |

Measured divergence at these calls: node 22 (V8 12.4) against Chromium 141 (V8 14.1), `Math.sin` and `Math.cos` one
ulp apart on a few arguments in a hundred; the owner's Firefox 157 against Chromium 141, `Math.hypot` on about a
quarter and `Math.sin` on one (R-6). `Math.atan2` was not seen to differ, but the language leaves its last bits to the
engine too, and it makes the bot's inputs and the fight's start, so rules 1 replace it with the others. Nothing else a
tick does is left to the engine: `+ - * / %`, comparisons, `Math.floor`, `ceil`, `min`, `max`, `abs`, `imul`, the bit
operators and `Math.PI` are fixed to the last bit by ECMA-262, and no numeric literal in `sim.js` has more than 20
significant digits (beyond 20 a literal's rounding is the engine's choice).

**The replacements.** In `sim.js`, built only from those operations, DataView's access to a double's bits, and BigInt:

- `xsin`, `xcos`: fdlibm 5.3's algorithm (`k_sin.c`, `k_cos.c`, the small and medium ranges of `e_rem_pio2.c`): the
  argument reduced by pi/2 in three parts of 33 bits (Cody and Waite), with a second and a third step when the first
  cancels, then the kernels' polynomials. Defined for |x| ≤ 2²⁰ · pi/2 (about 1.65 × 10⁶); beyond that they refuse
  with a `RangeError` rather than reduce wrongly. A tick's angles are wrapped to [0, 2 pi) or clamped to ±1.45.
- `xatan2`: fdlibm 5.3's `e_atan2.c` and `s_atan.c`, with FreeBSD's later correction (when |y/x| > 2⁶⁰ the result is
  ±pi/2 whatever the sign of x).
- `xsqrt`: correctly rounded, by an integer square root in BigInt; `Math.sqrt` is not used.
- `xhypot`: correctly rounded: the sum of the squares formed exactly in BigInt, then its square root as `xsqrt` takes
  one. No step overflows or underflows; the result is `Infinity` only when the rounded result is, and subnormal
  results are rounded as subnormals.
- Every constant is written as the bits of its double. fdlibm's decimals have 21 significant digits, and ECMA-262 lets
  an engine round a literal of more than 20 either way.

**Rules 0 kept.** `Sim.withRules(0)` builds the simulation as it was, calling the engine's functions, to measure the
old baseline against. Nothing plays it but the measurements and the trace.

**How it is held.**

- **`rules-arithmetic`** (a check): the 43 constants, fdlibm's to the last bit; each function over 4,000 arguments
  made from integers by one generator (ordinary angles and ratios, sums near multiples of pi/2, the edges of the
  kernels' branches, the tiny and the large, unit vectors, every binade from the subnormals to the largest double, and
  special values), every result's bits folded into a digest that must be the one `rules_ref.py` gives; 31 special
  values; the sine's domain refused. Plant: a sine one bit off at one argument.
- **`math-fence`** (a check): Math's 23 approximated functions made to throw, and the three runs recorded and played:
  the same state at every tick as without the fence. The source, read back by `Function.prototype.toString` up to the
  self-test, comments out and the rules-0 block set aside, names none of them. Plants: rules 0 under the fence; a tick
  that calls `Math.cos`.
- **`rules_ref.py`**: the same algorithms in Python, whose float is the same IEEE 754 binary64. It must give the
  digests and constants `sim.js` holds, the square root and hypot are checked exactly against the midpoints to their
  neighbours, and it measures the accuracy against 70 decimal digits.
- Eleven mutants of `sim.js` (a coefficient one bit off, the cosine's x/4 cut changed, no subnormal rounding, NaN
  before an infinity in hypot, no second reduction step, atan2 without FreeBSD's correction, the source scan blind, a
  tick calling `Math.hypot`, the sine's domain unguarded, the root's sticky bit ignored, the rules using the engine's
  `Math`): each refused by one of the two checks.

**Measured in the build container (2026-10-11).**

- The five functions, over 20,000 arguments each: the same bits under node 22 (V8 12.4), in Chromium 141 (V8 14.1) and
  in `rules_ref.py` (CPython). Node's own `Math.sin`, `Math.cos` and `Math.atan2` gave exactly the rules' bits on all of
  them; Chromium 141's `Math.sin` differed on 476 and `Math.cos` on 405; both engines' `Math.hypot` on 5,131 (not
  correctly rounded); `Math.sqrt` on none.
- Accuracy against 70 decimal digits (the first 1,000 arguments of each set): sine within 0.70 ulp, cosine 0.74,
  atan2 1.06 (fdlibm's own; a sweep of 20,000 found 1.23). The square root and hypot are correctly rounded on all
  4,000 of each.
- The trace, node against Chromium, on the same inputs: under rules 0 `Math.sin` and `Math.cos` differ on 112 and 99
  arguments and every state is still the same (rounding absorbed it); under rules 1 no call of the engine's Math, and
  every state of the three runs the same at every tick. In Chromium, rules 0 and rules 1 part on the stress run at tick
  490, in `x`, by one ulp, and meet again: rules 0's states there depend on Chromium's functions.
- Rules 1's replay of the walk ends at `91350c39A` on the tactical map and `ce819a52A` on the witness level, as rules
  0's baseline did: in these runs the engine's last bits were absorbed. That is a compatibility measurement, not the
  contract.
- A tick costs about 4.2–4.6 µs under rules 1 and 1.4 µs under rules 0, under node (BigInt's exact hypot, called once a
  moving tick); at 120 ticks a second, about half a millisecond a second.

**A second implementation of the tick** (`tick_ref.py`, written from [`RULES-1.md`](RULES-1.md)). By the owner's
ruling of 2026-10-11: the browser records the inputs, Python advances the authoritative state on its own, and each
tick's snapshot is compared with the browser's; the first that differs names its tick and its fields. It shares the
specification and the arithmetic's algorithms with `sim.js`, and, since 0255, its door's run set, a reading of
`sim.js`'s `makeRuns` and `lines()` by one author (the walk is `bot_ref.py`'s); nothing else: its own state (classes, not a walked
object), world, collision and ray walks, snapshot writer and reader, and its own square root and hypot (Python's
integer square root). It reads a trace, converts the map the trace names and holds it to the trace's manifest,
and, at its door (VERIFY-DOOR-0, 0255), makes every run the browser was to play from the map alone (the walk by
`bot_ref.py`, the fight by a reading of `lines()` and `makeRuns`, the stress run from integers) and refuses a trace
whose runs, starts, lengths or inputs are not those, or that holds a number that is not finite or one its readers
cannot read, each with its own code; then it plays every rules-1 run from its start (a run whose start or inputs are
not the ones made here is not played: a FAIL row). Measured in
the build container: Chromium 141's traces and node 22's, on both maps, 5,863 and 5,247 ticks, every snapshot the
same bytes as the browser's; and on the owner's machine, Firefox 157's own trace of the tactical map (5,863 ticks). Its self-test plants a field one bit off and an input changed (each found at its tick), and at the door the stress
run renamed and cut to 2 (refused by VERIFY-RUN-SET; `doortest` holds the rest of the door),
and six defects in the Python tick (the height's updates in the wrong order, five halvings for six, the shot's
direction with the wrong sign, a target standing again at 0, the sine's polynomial cut short, the cells scanned from
the centre), each found. A defect of one place in the last bit can be absorbed by a run: the plain root of the sum
for hypot parts from the browser on the tactical walk at tick 1172 and never on the witness level's runs. So the
tick is held here and the arithmetic, result by result, in `rules_ref.py`.

**The walk made in Python** (`bot_ref.py`, written from [`WALK-1.md`](WALK-1.md)). By the owner's ruling of 2026-10-11
(BOT-REF-0): the map, the bot's policy (`walk-1`) and rules 1 make the walk's inputs in Python, and `tick_ref.py`
advances them, so that no browser is needed to originate the reference walk. The bot is a policy apart from the
rules. Before each input it is given an observation of the present state (`x`, `z` and `yaw`) and nothing else; it
never sees a later state or a browser's decision, and the tick is `tick_ref.py`'s. `WALK-1.md` writes down the policy
`sim.js`'s bot had followed, with the choices it had left unsaid: the route taken by name order, the targets' cells
closed to the plan, the plan's climb read from cell top to cell top, the turn taken whole and the short way, a cell
reached within 0.3 m at the cost of a decision and no tick, and the stall rule. The walk is written as
`VERDANDI-BOT-TRACE 1`: the map's identity, the start's bytes, the rules, the policy, the number of ticks, each tick's
input and a digest. A reader refuses the whole file on any malformed or mismatched part, with a code for each.
`check` makes the walk again and holds it to what a walk is for (its inputs, its path, its replay); `compare` sets it
beside a browser's trace, tick by tick and field by field; `trace.py run --inputs BOT.json` has a browser play it.
Measured in the build container, on the tactical map: the walk made three times, the same bytes (here, and in two
fresh processes under other hash seeds); its start and 1,787 inputs the same bytes as the walk Chromium 141's own
bot records; Chromium 141 and node 22 playing it, every snapshot the same bytes as the Python tick's. On the owner's
machine: the same file made twice; the same start, inputs and states as his Firefox 157's own bot's walk; Firefox 157
and Edge 155 playing it, every snapshot the Python tick's. Its self-test
plants six defects in the policy, one changed byte of an input, two changes to the map's identity, ten faults of
form, a tick's result one bit off, and walks that break each property a walk is held to, and each is found. Five
more plants are reported, not required: four leave this walk byte for byte the same (±x searched in the other order,
the targets' cells left open, a stall after 18 ticks, the plain root of the sum for the distance), and one depends on
the machine's C library (the platform's atan2). The witness level waits until the tactical walk has passed on the owner's machine.

**What is not shown.** That every engine gives the same bits: ECMA-262 requires it of the operations rules 1 use, and
the owner's Firefox 157 passed `rules-arithmetic` (its results on all 20,000 arguments as CPython's) and gave the same
digest of every tick's state as Chromium 141 and node 22 on the tactical map's three runs; on his machine, Firefox 157
and Edge 155 then played the same recorded inputs, and every rules-1 snapshot was the same bytes at every tick of
those three runs (MEASURED once, 2026-10-11; by the owner's ruling of that day, cross-browser equivalence on the tactical map
advanced from NOT ESTABLISHED to MEASURED once). Not the witness level, not JavaScriptCore, not every build.
That an engine has no bug in those operations. That a future change to `sim.js` keeps to the contract, beyond what
the checks, the plants and the second implementation catch. Anything about a server's security or a network.

The trace experiment (`trace.py`) is where cross-engine differences are pinned down. It is a diagnostic beside the self-test, not part of it,
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
| `trace.py` | the trace experiment: its own small launcher (four files and the map, and with `--inputs` the runs of another trace or a walk `bot_ref.py` made), and the comparison of two traces, rules by rules |
| `rules_ref.py` | the reference for the rules' arithmetic: the same algorithms in Python, and what holds `sim.js` to them |
| `RULES-1.md` | the tick as arithmetic: the specification `sim.js` and `tick_ref.py` are both written to |
| `RULES-2.md` | rules 1 with movers, and the hash bound to the rules, the constants and the world (0225) |
| `web/rules2_cases.json` | rules 2's table: eleven cases with values worked by hand from `RULES-2.md`, and two long runs among three movers held between the implementations |
| `RULES-3.md` | rules 2 with solid walls, a standing target's top as ground, a target that waits for its column to clear, and the mover policy push (0228) |
| `web/rules3_cases.json` | rules 3's table: fourteen cases with values worked by hand from `RULES-3.md` (and what rules 2 do with the same inputs), and two long runs among three pushers held between the implementations |
| `tick_ref.py` | the tick's second implementation, in Python, and the verifier of a browser's trace, with its door (VERIFY-DOOR-0, 0255) |
| `ORT-1.md` | ORT-1: a rules-2 world's origin, and its rebase between two ticks as a transition bound to its basis (0227) |
| `ort_ref.py`, `web/ort.js`, `web/ort_cases.json` | ORT-1's two implementations, Python and JavaScript, written apart, and its table of cases worked by hand |
| `translate_probe.py` | a measurement, not a check (0225): rules 1's stress run with the world moved by 2^7 to 2^23 m along x and z, set against the unmoved run tick by tick; it writes nothing and no check reads it |
| `web/input_cases.json` | the input contract's table: 70 cases of hostile and admitted inputs, each step's required outcome, held to by `sim.js` (the self-test's `input-contract`, `trace.py run --cases`) and `tick_ref.py cases` |
| `WALK-1.md` | the bot's policy, `walk-1`: the walk as inputs chosen from the map and an observation of the present state; the specification `sim.js`'s bot and `bot_ref.py` are both written to, and the walk's file |
| `bot_ref.py` | the walk made in Python from the map alone, its checks, and its comparison with a browser's trace |
| `web/sim.js` | the simulation: movement, collision, gravity, the weapon, the targets, the state's snapshots, the rules' arithmetic (rules 1; rules 0 kept for comparison; rules 2, movers), the self-test. No DOM; runs in a worker and under node too |
| `web/sim_worker.js` | the simulation in a realm of its own, for the self-test and the trace: resumes a snapshot, plays a run in a counterfactual engine, or plays the three runs under both rules with Math logged |
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
GPU's completion), before anything is composited, and are not input-to-photon. Determinism within one browser is
checked: the replay compares two runs in the same page, and the state checks above say what its equal hashes cover.
Across browsers and machines, rules 1 are built to give the same bits (the contract above): measured the same in two
V8 engines and against CPython, and on the owner's machine in Firefox 157 and Edge 155 as their pages report themselves
(corrected 0255: this said "not yet measured in another engine", which the measurements above had made false).

## Boundaries

See [`docs/BOUNDARIES.md`](../docs/BOUNDARIES.md). In short: the simulation moves against the collision world and
reads no render data; the renderer reads the state and writes none of it, and decorates without deciding what blocks;
the weapon in the hand is drawn apart from the shot, which leaves from the eye; input reaches the simulation only as
a tick's input record.
