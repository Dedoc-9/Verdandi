<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The graybox's bot, policy `walk-1`: a route walked by inputs alone

This is the specification of the bot that makes the walk run. The walk run is the first of the three runs the
self-test replays and `trace.py` records: one of the map's routes, walked end to end through the rules' movement. Two
implementations are written from it. `web/sim.js` (`walkGraph`, `routePath`, `walk` and `record`) is where the policy
was first written. `bot_ref.py`, in Python, was written from this text by the owner's ruling of 2026-10-11 (BOT-REF-0),
so that a browser is no longer needed to originate the reference walk.

The bot is a policy, not a part of the rules. It chooses each tick's input. The tick ([`RULES-1.md`](RULES-1.md)) alone
advances the authoritative state. Before each input the bot is given an **observation** of the present state: `x`,
`z` and `yaw`, nothing else. It never sees a later state, a browser's decision, or another trace. Its version
(`walk-1`) is apart from the rules' (`1`), and a walk names both.

The arithmetic is the rules': each operation rounded and evaluated as written; `hypot`, `atan2`, `π` and `wrap` as
`RULES-1.md` defines them.

## What it reads

From the map the server sends (`graybox/level.py`'s conversion): `w`, `h`, `cell` and `tops` from the collision world,
and `top(i, j)` as `RULES-1.md` defines it (`+∞` outside the grid); `wall` (the walls' height), `routes` (each a name and
its waypoints, cells `(i, j)`), `targets` (their cells) and the spawns, from the canonical world.

## The routes, in order

The routes are taken in the order of their names, compared by UTF-16 code units, as JavaScript's default sort compares
strings. This is not quite Python's order for strings: the two differ when a name holds a character above U+FFFF. For
each route in turn:

1. Its **path** is made from its waypoints (below). If some waypoint cannot be reached from the one before it, the
   route is passed over.
2. A **start** is made at its first waypoint, and the path is **walked** from it (below). If the walk ends, its inputs
   are the walk run, and no later route is tried. If it fails, the next route is tried.

If no route's walk ends, there is no walk run.

## A path between two cells

A cell is **open to the bot** when `top(i, j) < wall` and no target is defined on it. A target that is down does not
open its cell, because the plan is made from the map, not from a state.

The path from `a` to `b` is a breadth-first search from `a`. A cell's neighbours are taken in this order: `(i + 1, j)`,
`(i − 1, j)`, `(i, j + 1)`, `(i, j − 1)`. A neighbour is reached from a cell when it is open, has not been reached
already, and `top(neighbour) − top(cell) ≤ step` (0.55; there is no limit going down). `a` itself counts as reached at
the outset, open or not. Each reached cell remembers the cell it was first reached from, and the search ends when `b`
is reached or nothing more can be. If `b` was reached, the path is `a`, …, `b` along those remembered cells. If not,
there is no path.

A route's path is its first waypoint, then each leg's path from one waypoint to the next without the leg's first cell.
A leg from a cell to the same cell adds nothing.

## The start

A new state for side A, as `RULES-1.md` makes one (so the yaw is spawn A's), then, with the first waypoint `(i0, j0)`:
`x = (i0 + 0.5)·cell`, `z = (j0 + 0.5)·cell`, `feet = groundAt(x, z)`. The run's start is that state's snapshot.

## Walking a path

The bot keeps its own state, apart from the game's: `k`, the index in the path of the cell it is heading for (1 at the
outset); `best`, the least distance to it seen so far (`+∞`); `still`, the number of ticks without progress (0); and `n`,
the number of decisions made (0). The limit is `L = 120 · (the path's length) + 600` decisions.

Each decision, given the observation `(x, z, yaw)`:

1. If `n = L`, the walk **fails**.
2. If `k` is the path's length, the walk **ends**.
3. The target point is the centre of the path's cell `k`, `(tx, tz) = ((i + 0.5)·cell, (j + 0.5)·cell)`; `dx = tx − x`,
   `dz = tz − z`, `dist = hypot(dx, dz)`.
4. If `dist < 0.3`: the cell is reached; `k = k + 1`, `best = +∞`, `still = 0`, `n = n + 1`, and the bot decides again
   **without a tick**.
5. Otherwise the input is `{f: true, dyaw: d}` with `want = atan2(dx, −dz)`, `d = wrap(want − yaw)`, and then
   `d = d − 2π` if `d > π` (`2π` being `2·π`). The tick is played with it.
6. Then, with the `dist` of step 3 (the distance before the tick): if `dist < best − 1e-6`, `best = dist` and
   `still = 0`; otherwise `still = still + 1`, and if `still > 180` the walk **fails**. Then `n = n + 1`.

The walk's inputs are the inputs of step 5, in order.

## What `walk-1` assumes

These are choices of this policy, not of the rules. A second implementation that copied the first without naming
them would inherit them unseen:

- The route is the first in name order that can be walked, not a chosen one; the start is its first waypoint, not a
  spawn, but the yaw is spawn A's.
- The plan reads the map's heights cell to cell (a climb of at most `step` between two cells' tops), not the rules'
  collision, which tests a circle of radius 0.35 against every cell it overlaps. A path the plan allows can still be
  blocked in play, and the walk then fails on the stall limit.
- Every target's cell is closed to the plan, standing or not.
- The bot turns the whole way toward its next cell in one tick, the short way round (`d` in `(−π, π]`), and only ever
  walks forward: no strafe, no jump, no shot, no look up or down.
- A cell counts as reached within 0.3 m of its centre. Reaching one costs a decision and no tick, and the limit `L`
  counts decisions.
- Progress is the distance measured before the tick. The walk fails after more than 180 ticks without coming 10⁻⁶ m
  closer.

## The trace, `VERDANDI-BOT-TRACE 1`

A walk is written as one JSON object, keys sorted, no spaces, followed by one newline. Its keys are exactly these:

| key | value |
|---|---|
| `format` | `"VERDANDI-BOT-TRACE"` |
| `version` | `"1"` |
| `map` | the map's name |
| `manifest` | `{"canonical_sha256": …, "collision_sha256": …}`: the map's identity, as `level.py`'s manifest gives it |
| `rules` | `"1"` |
| `policy` | `"walk-1"` |
| `route` | the route walked |
| `runs` | one run: `{"inputs": […], "name": "the walk", "start": …, "ticks": N}`: the start's snapshot (`RULES-1.md`, *The snapshot*), the number of ticks, and each tick's input as `RULES-1.md`'s *The inputs* writes it |
| `digest` | the sha256 of the object without `digest`, written the same way, as 64 lower-case hex digits |

A reader refuses the whole file when any of this does not hold: other bytes than that writing; a key missing or
added; a format, version, rules or policy it does not know; a map whose conversion here has other digests; a run
other than one named `the walk`; `ticks` other than the number of inputs; an input not written as the inputs are
written; a start not written as a snapshot is written; a digest that is not the body's.

## What a walk is held to

Checked from the map and a replay of the walk through the tick, by code apart from the policy's:

- **The inputs.** Each holds exactly `f`, true, and `dyaw`, finite, in `(−π, π]`.
- **The path.** It begins at the route's first waypoint and ends at its last, passes every waypoint in order, steps
  from cell to neighbouring cell, keeps to the grid, to cells below the walls' height and off the targets' cells, and
  climbs at most `step` a step.
- **The walk.** Played from its start, it ends within 0.3 m of the centre of the route's last waypoint, has stood in
  every waypoint's cell in order on the way, and is shorter than its limit.

These say the walk does what a walk of the route is for. They do not say that `walk-1` is the walk a player would
make.
