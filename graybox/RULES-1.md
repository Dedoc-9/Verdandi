<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The graybox's rules, version 1: the tick as arithmetic

This is the specification two implementations are written from: `web/sim.js` (JavaScript, in the browser) and
`tick_ref.py` (Python, independent of it). It says what the authoritative state is, what one tick does to it, and in
what order and with which operations, because two programs reach the same bits only if every rounding is the same
rounding. Where it and `sim.js` disagree, one of them is wrong; the verifier (`tick_ref.py verify`) is how that is
found. The contract around it — what must be the same in every engine, what need not — is in
[`README.md`](README.md), *The simulation's contract*.

## Arithmetic

Every number is an IEEE 754 binary64 double. `a + b`, `a − b`, `a × b`, `a ÷ b` round to nearest, ties to even, and
are evaluated left to right as written (`a × b × c` is `(a × b) × c`); nothing is fused or reassociated. Besides those:

| written | means | note for an implementation |
|---|---|---|
| `floor(x)` | the greatest integer ≤ x, as a double; `floor(−0) = −0` | Python's `math.floor` returns an int and loses −0 |
| `fmod(a, b)` | `a − b·q`, q the integer quotient truncated toward 0, exact (C's `fmod`, JavaScript's `%`) | Python's `%` is not this |
| `max(a, b)`, `min` | JavaScript's `Math.max`, `Math.min`: NaN if either is NaN; `max(+0, −0) = +0`, `min(+0, −0) = −0` | |
| `abs(x)` | the magnitude | |
| `sin`, `cos`, `atan2`, `hypot`, `sqrt` | the rules' own (`xsin`, … in `sim.js`, the same algorithms in `rules_ref.py`); never an engine's | fdlibm 5.3's sine, cosine and atan2; correctly rounded square root and hypot |
| `π` | the double nearest π (`0x400921FB54442D18`) | |
| `TICK` | `1 ÷ 120` | |
| an input's flag | the field's value, true or false; false when it is absent | an admitted input holds no other value (*The input*, below) |
| an input's number `dyaw`, `dpitch` | the field's value, or `+0` when it is absent, `0` or `−0` (JavaScript's `x || 0`) | an admitted input holds no NaN or infinity (*The input*) |

## The constants

`radius 0.35`, `eye 1.62`, `step 0.55`, `speed 6.0`, `gravity 20.0`, `jump 7.0`, `fireCooldown 0.12`,
`targetRadius 0.4`, `targetHeight 1.9`, `targetDown 2.5`, `range 200`; the pitch's limit `1.45`; a target stands again
when its `downFor ≤ 1e-9`. (These are `sim.js`'s `P`, whose declaration `art/check.py` also reads.)

## The world

From the map the server sends (`graybox/level.py`'s conversion): `w`, `h`, `cell` and `tops` from the collision
world; `wall`, `spawns`, `objective` and `targets` from the canonical world. `top(i, j)` is `tops[j·w + i]` inside the
grid and `+∞` outside it.

`touching(x, z, r)`: the cells `(i, j)` for `i` from `floor((x − r) ÷ cell)` to `floor((x + r) ÷ cell)` and `j` from
`floor((z − r) ÷ cell)` to `floor((z + r) ÷ cell)` such that, with `px = max(i·cell, min(x, (i + 1)·cell))`,
`pz = max(j·cell, min(z, (j + 1)·cell))`, `dx = x − px`, `dz = z − pz`: `dx·dx + dz·dz < r·r`.

`blocked(state, x, z, feet)`: some cell of `touching(x, z, radius)` has `top > feet + step`; or some standing target
`t` has, with `dx = x − t.x`, `dz = z − t.z`, `rr = radius + targetRadius`: `dx·dx + dz·dz < rr·rr` and
`feet < t.y + targetHeight`.

`groundAt(x, z)`: the greatest `top` over `touching(x, z, radius)`, starting from `0` (so never below 0; `+∞` at the
grid's edge).

## The state

`tick`, `side` ("A" or "B"), `x`, `z`, `feet`, `vy`, `yaw`, `pitch`, `onGround`, `cooldown`, `score`, `shots`,
`onObjective`, and `targets`, in the map's order, each `{id, x, y, z, up, downFor}`. Nothing else is authoritative
(the page's `fx` is the view's).

A new state for a side: every number 0 but as below, `onGround` true, `onObjective` false; each target at
`x = (tx + 0.5)·cell`, `z = (tz + 0.5)·cell`, `y = top(tx, tz)`, standing, `downFor 0`; then `spawn(side)`.

`spawn(side)`: with the side's spawn `(sx, sz, yawDegrees)`: `side`; `x = (sx + 0.5)·cell`; `z = (sz + 0.5)·cell`;
`feet = groundAt(x, z)`; `vy = 0`; `onGround` true; `yaw = yawDegrees·π ÷ 180`; `pitch = 0`.

## The input (contract 1)

Before a tick, its input is admitted or refused, whole. A refused input changes nothing: not the state, not its count
of ticks. The tick runs only on an admitted input, and on every admitted input it is the tick below, bit for bit. The
contract has its own version, 1, apart from the rules'; INPUT-CONTRACT-0 (the owner's ruling of 2026-10-11) wrote it.

An input is admitted when it is a **record** (in JavaScript a plain object: its prototype null or an
`Object.prototype`, of any realm; in Python a `dict`) and each of its own fields, taken in the order of their names by UTF-16 code units, is one
of these:

| field | admitted values | when it is absent |
|---|---|---|
| `f`, `b`, `l`, `r`, `jump`, `fire`, `reset` | `true` or `false` | false |
| `side` | `"A"` or `"B"` | the side is not changed |
| `dyaw`, `dpitch` | a finite number: a binary64 double (in Python a `float`) that is not NaN, `+∞` or `−∞` | `+0` |

No field is required: an empty record is a tick with nothing pressed, as the recorded runs have always had. A finite
number of any magnitude is admitted: the yaw is reduced by `fmod`, exact for every finite double, and the pitch is held
to ±1.45, so a turn of the largest double is a defined tick (`web/input_cases.json` holds both implementations to it).
`−0` is taken as `+0`.

Otherwise the input is refused, with the category of its first fault: first whether it is a record at all, then its
fields in the order of their names, and in each field the first rule of the table it breaks:

| category | the fault |
|---|---|
| `INPUT-NOT-RECORD` | the input is not a record: null, a number, a string, a boolean, a list, an object of another kind |
| `INPUT-UNKNOWN-FIELD` | a field with another name (`crouch`, `F`, `__proto__`, the empty name, …) |
| `INPUT-FLAG` | a flag that is not `true` or `false` (`0`, `1`, `"true"`, null, a list, …) |
| `INPUT-SIDE` | a side that is not `"A"` or `"B"` |
| `INPUT-NUMBER` | `dyaw` or `dpitch` that is not a number |
| `INPUT-NOT-FINITE` | `dyaw` or `dpitch` that is NaN, `+∞` or `−∞` |

Two implementations agree on an input when both admit it and reach the same next state, or both refuse it with the
same category and leave the state as it was. The words of an error and the kind of exception are not part of the
contract. Non-finite numbers are refused rather than carried: a NaN that reaches the state stays in it, and ECMA-262
lets each engine choose the bits it writes for a NaN, so a state that holds one has no single snapshot; an infinite
turn makes the yaw NaN. The pitch's infinities, which its limit would hold, are refused too, so that every number in
an input has one rule. The record is read once: the tick reads the values the check admitted, not the record again.

The cases both implementations are held to, and the category each refusal must have, are in
[`web/input_cases.json`](web/input_cases.json).

## One tick

On an admitted input (*The input*, above), in this order:

1. `tick = tick + 1`.
2. If the input names a `side`: `spawn(side)`; else if `reset`: `spawn(the state's side)`.
3. `yaw = wrap(yaw + dyaw)`, where `wrap(a) = fmod(fmod(a, 2π) + 2π, 2π)` and `2π` is `2·π`.
4. `pitch = pitch + dpitch`, then held to `[−1.45, 1.45]`: below −1.45 it is −1.45, above 1.45 it is 1.45.
5. Walking. `fwd = (f ? 1 : 0) − (b ? 1 : 0)`, `side = (r ? 1 : 0) − (l ? 1 : 0)`; `sy = sin(yaw)`, `cy = cos(yaw)`;
   `mx = fwd·sy + side·cy`; `mz = (−fwd)·cy + side·sy`; `len = hypot(mx, mz)`. If `len > 0`:
   `mx = mx ÷ len · speed · TICK`, `mz = mz ÷ len · speed · TICK`, then `move(mx, 0)` and `move(0, mz)`.
   `move(dx, dz)`: if not `blocked(x + dx, z + dz, feet)`, `x = x + dx`, `z = z + dz`; otherwise six times: `dx = dx ÷ 2`,
   `dz = dz ÷ 2`, and if not `blocked(x + dx, z + dz, feet)`, `x = x + dx`, `z = z + dz`.
6. Height. `was = onGround`. If `jump` and `onGround`: `vy = jump`, `onGround` false. `vy = vy − gravity·TICK`;
   `feet = feet + vy·TICK`; `g = groundAt(x, z)`. If `feet ≤ g`, or `was` and `vy ≤ 0` and `feet − g ≤ step`:
   `feet = g`, `vy = 0`, `onGround` true; otherwise `onGround` false.
7. The weapon. `cooldown = max(0, cooldown − TICK)`. If `fire` and `cooldown = 0`: `cooldown = fireCooldown`, and fire.
8. Each target not standing: `downFor = downFor − TICK`; if `downFor ≤ 1e-9`, it stands and `downFor = 0`.
9. `onObjective`: with an objective `(i0, j0, i1, j1)`, `i = floor(x ÷ cell)`, `j = floor(z ÷ cell)`:
   `i0 ≤ i ≤ i1` and `j0 ≤ j ≤ j1`; false without one.

**Firing.** `shots = shots + 1`. `cp = cos(pitch)`; the direction `d = (cp·sin(yaw), sin(pitch), (−cp)·cos(yaw))`;
the eye `o = (x, feet + eye, z)`. `bt` is the wall's distance along `d` (below), up to `range`. Each standing target, in
order, is the box `[t.x − targetRadius, t.x + targetRadius] × [t.y, t.y + targetHeight] × [t.z − targetRadius,
t.z + targetRadius]`; if its entry distance `tt < bt`, then `bt = tt` and it is the one hit (so a later target at the
same distance does not replace it). The target hit, if any: not standing, `downFor = targetDown`, `score = score + 1`.

**The wall's distance** (a walk of the cells the ray crosses in x–z; a cell is solid from 0 to its top). `i =
floor(ox ÷ cell)`, `j = floor(oz ÷ cell)`; `si = 1` if `dx > 0` else −1, `sj` likewise; `tdx = abs(cell ÷ dx)` if
`dx ≠ 0` else `+∞`, `tdz` likewise; `tmx = ((i + 1)·cell − ox) ÷ abs(dx)` if `dx > 0`, `(ox − i·cell) ÷ abs(dx)` if
`dx < 0`, `+∞` if `dx = 0`; `tmz` likewise; `t0 = 0`. Then, at most 10,000 times and while `t0 < range`:
`t1 = min(tmx, tmz, range)`; if `top(i, j) = +∞` the distance is `t0`; `y0 = oy + dy·t0`, `y1 = oy + dy·t1`; if
`y0 ≤ top` the distance is `t0`; if `y1 ≤ top` it is `(top − oy) ÷ dy`; then if `tmx < tmz`: `i = i + si`, `t0 = tmx`,
`tmx = tmx + tdx`; else `j = j + sj`, `t0 = tmz`, `tmz = tmz + tdz`. If the walk ends, the distance is `range`.

**A box's entry distance.** `tn = −∞`, `tf = +∞`; for each axis in the order x, y, z, with the eye's coordinate `o`,
the direction's `d` and the box's `lo`, `hi`: if `d = 0` (either zero) and `o < lo` or `o > hi`, the distance is `+∞`;
if `d = 0` otherwise, the axis is skipped; else `ta = (lo − o) ÷ d`, `tb = (hi − o) ÷ d`, swapped if `ta > tb`;
`tn = ta` if `ta > tn`; `tf = tb` if `tb < tf`; if `tn > tf` the distance is `+∞`. At the end: `+∞` if `tf < 0`,
else `max(tn, 0)`.

## The snapshot

The state as JSON: an object whose keys are in sorted order (each target's too), with no spaces; every number written
as `"f"` and the 16 lower-case hex digits of its bits, big-endian (so −0 and the last bit survive); every string as
`"s"` and the string; booleans as `true` and `false`. Two implementations agree on a state when their snapshots are
the same bytes.

## The inputs

A tick's input as the trace writes it: a JSON array of `[field, value]` pairs in sorted order, a number written as
`"f"` and its bits as above, a flag as `true` or `false`, a side as the bare string. The stress run's inputs are made
from integers alone (`sim.js`, `stressInputs`), so any implementation can make them again.
