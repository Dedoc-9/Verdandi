<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The graybox's rules, version 2: movers

Rules 2 are [rules 1](RULES-1.md) with **movers**: boxes that slide back and forth along one axis, carry a player who
stands on them, and stop rather than move into a player. Everything rules 1 say holds under rules 2 except where this
document says otherwise. Like rules 1, it is the specification two implementations are written from, `web/sim.js`
(rules 2, `GrayboxSim.withRules(2)`) and `tick_ref.py` (`rules2`); where they disagree, one of them is wrong.

By the owner's rulings of 2026-10-13: the mover step is a slot in the tick, one code path (a world without movers is
played by the same tick); a parked mover equals a static box; the rules' version is a constant in both
implementations, bound into every tick's hash; and, of RULES-2's acceptance, *"complete state identity (rules version
and all parameters, gravity and timestep, in every tick hash); defined integer semantics; independent answers"*.

## Arithmetic

Rules 1's, unchanged. One more constant: `Q`, a phase unit, `1 ÷ 256` metres (the double `0x3F70000000000000`).

**Integer semantics.** A mover's `phase`, `len`, `speed` and axis are integers, held exactly as doubles. A mover's box
coordinates are multiples of `Q` with magnitude below 1,024 m. So every number a mover's pose is made of —
`o·Q`, `ax·(o·Q)`, `x0 + ax·(o·Q)`, and a pose's difference from another — is a multiple of `Q` below 2^11 in
magnitude, which a double holds exactly: none of the mover arithmetic rounds, in any engine. The player's numbers
are rules 1's doubles; a rider is moved by adding a mover's exact displacement to them, which rounds as any `+` does.

## The constants

Rules 1's, and `height 1.8`, the body: a player occupies the column from `feet` to `feet + height` (the art layer's
`BODY`). `height` is used only with movers; rules 1's cells are columns from 0 to their top, and the body's height
never mattered against them.

## The world

Rules 1's, and `movers`, in the map's order (none: an empty list). Each mover:

| field | what | refused (`RULES2-MOVER`) unless |
|---|---|---|
| `id` | its name | text, unique among the movers |
| `box` | `x0, y0, z0, x1, y1, z1`, metres, its pose at phase 0 | each a multiple of `Q`, magnitude below 1,024; `x0 < x1`, `y0 < y1`, `z0 < z1` |
| `axis` | `ax, ay, az` | integers, exactly one of them non-zero, and it `1` or `−1` |
| `len` | how far it travels one way, in phase units (`Q` metres each) | an integer, `1 ≤ len ≤ 2^18` |
| `speed` | phase units a tick | an integer, `0 ≤ speed ≤ len`, and **within the tunnelling bound** (below) |
| `policy` | what it does when it meets a player | `"stop"` (the only policy of rules 2) |

**The tunnelling bound.** A mover must not be able to pass through a player between two ticks without either tick
seeing them overlap. Along `x` or `z` a box of thickness `t` (its extent along its axis) passes a circle of radius
`radius` only if it moves at least `2·radius + t` in one tick; along `y` it passes the body only if it moves at least
`height + t`. So a world is refused unless `speed·Q < 2·radius + t` (axis `x` or `z`) or `speed·Q < height + t`
(axis `y`), each side computed as written. (The probe of 2026-10-13 measured passes from 0.96 m a tick and none below
0.95 m, for a slab 0.25 m thick: `2·0.35 + 0.25`.)

A mover's **pose** at a phase `p` (`0 ≤ p < 2·len`): `o = p` if `p < len`, else `o = 2·len − p` (so it goes out to
`len` and back); `d = o·Q`; the box `x0 + ax·d, y0 + ay·d, z0 + az·d, x1 + ax·d, y1 + ay·d, z1 + az·d`.

Movers do not meet the world's cells or each other: the art layer refuses a world whose movers' swept boxes meet rock,
a spawn's column, or each other's (that check is the exporter's, not the tick's).

## The state

Rules 1's, and `movers`, in the world's order, each `{phase, stopped}`: `phase` an integer, `0 ≤ phase < 2·len`;
`stopped` true when the mover held still last tick because moving would have entered a player. A new state: every
mover at phase 0, not stopped. `spawn` is rules 1's: it stands the player on the cells, never on a mover.

**The snapshot** is rules 1's, with `movers`: a list, each `{"phase": …, "stopped": …}` (keys sorted, the number as
`"f"` and its bits). Two implementations agree on a state when their snapshots are the same bytes.

## The body against movers

`over(x, z, b)`: the circle of radius `radius` at `(x, z)` overlaps the box `b` in plan, strictly: with
`px = max(b.x0, min(x, b.x1))`, `pz = max(b.z0, min(z, b.z1))`, `dx = x − px`, `dz = z − pz`: `dx·dx + dz·dz < radius·radius`.

`boxes`: every mover's pose at its phase, in the world's order.

`blocked(x, z, feet)` is rules 1's, or some box `b` has `over(x, z, b)`, `b.y1 > feet + step` and `b.y0 < feet + height`:
a box the player cannot step onto that reaches into the body.

`ground(x, z, before)`: rules 1's `groundAt(x, z)`, raised to `b.y1` for every box `b` with `over(x, z, b)` and
`b.y1 ≤ before + step`: the tops at or under the body, as high as a step above `before`.

`ceiling(x, z, before)`: the least `b.y0` over the boxes with `over(x, z, b)` and `b.y0 ≥ before + height` (wholly
above the head), `+∞` when there is none.

## One tick

On an admitted input (rules 1's contract, version 1, unchanged), in this order:

1. `tick = tick + 1`.
2. As rules 1's step 2 (`side`, `reset`).
3. **The movers**, each in the world's order, as below.
4. to 6. As rules 1's steps 3 to 5 (the yaw, the pitch, walking), with `blocked` as above.
7. Height. `was = onGround`; `before = feet`. If `jump` and `onGround`: `vy = jump`, `onGround` false.
   `vy = vy − gravity·TICK`; `feet = feet + vy·TICK`. With `c = ceiling(x, z, before)`: if `feet + height > c`, then
   `feet = c − height` and, if `vy > 0`, `vy = 0`. With `g = ground(x, z, before)`: if `feet ≤ g`, or `was` and
   `vy ≤ 0` and `feet − g ≤ step`: `feet = g`, `vy = 0`, `onGround` true; otherwise `onGround` false.
8. to 10. As rules 1's steps 7 to 9 (the weapon, the targets, the objective).

**A mover's step.** With its phase `p`: `n = p + speed`, and `n = n − 2·len` if `n ≥ 2·len`. `a` is its pose at `p`,
`b` its pose at `n`; `dx = b.x0 − a.x0`, `dy = b.y0 − a.y0`, `dz = b.z0 − a.z0` (exact). If `speed = 0`, nothing
changes and `stopped` is false: **a parked mover is a static box**. Otherwise:

- **A rider** is a player with `onGround`, `feet = a.y1` and `over(x, z, a)`. The rider's new place is
  `(x + dx, z + dz, feet + dy)`; with this mover at `b` and the others where they stand, if that place is not
  `blocked`, then `phase = n`, `x = x + dx`, `z = z + dz`, `feet = feet + dy` and `stopped` is false; otherwise nothing
  moves and `stopped` is true. (Its own top is under the rider's new feet, never above a step: it does not block.)
- **Not a rider:** if `b` reaches into the body — `over(x, z, b)`, `b.y1 > feet` and `b.y0 < feet + height` — nothing
  moves and `stopped` is true (policy `stop`); otherwise `phase = n` and `stopped` is false.

A shot is rules 1's: it meets the cells and the targets, not the movers (a mover does not stop a shot in rules 2).
A rider who jumps or walks off keeps nothing of the mover's motion: the player has no horizontal velocity in rules 1
or 2, and a mover's vertical motion is not added to `vy`. A rider carried up into a box above stops the mover.

## The state's hash, and what it is bound to

Rules 2's hash is FNV-1a with 64 bits (offset `0xcbf29ce484222325`, prime `0x100000001b3`, each step `h = (h xor byte)
× prime mod 2^64`), over:

1. **the identity**: the UTF-8 bytes of `VERDANDI-RULES 2` and a line feed, then the identity document (below);
2. rules 1's list of numbers, each as 8 bytes little-endian;
3. then, for each mover in order, its `phase` and `stopped ? 1 : 0`, likewise.

It is written as 16 lower-case hex digits and the side. **The identity document** is JSON with no spaces, every
number written as `"f"` and its 16 hex digits (as the snapshot writes them), every string as `"s"` and the string:

```
{"P":{"eye":…,"fireCooldown":…,"gravity":…,"height":…,"jump":…,"radius":…,"range":…,"speed":…,"step":…,
      "targetDown":…,"targetHeight":…,"targetRadius":…},
 "Q":…,"TICK":…,"input":…,"pitch":…,"rules":…,"stand":…,
 "world":{"cell":…,"h":…,"movers":[[id,x0,y0,z0,x1,y1,z1,ax,ay,az,len,speed,policy],…],
          "objective":[i0,j0,i1,j1] or null,"spawns":{"A":[x,z,yawDegrees],"B":[…]},
          "targets":[[id,x,z],…],"tops":[…],"w":…}}
```

(`input` is the input contract's version, 1; `pitch` the pitch's limit, 1.45; `rules` 2; `stand` the 1e-9 a target
stands again at.) So the rules' version, every constant — gravity and the timestep among them — the map and every mover
enter every tick's hash: two runs whose hashes agree played the same rules on the same world, or met a collision of
FNV-1a. The identity's own FNV-1a 64 is reported beside a run (`identity`), so a difference between two runs is told
apart as a difference of world or rules before any tick is compared. The snapshot, not the hash, is the state's
identity for the checks; the hash is the cheap comparison a replay makes.

## The independent answers

`web/rules2_cases.json` holds scenarios (a map, its movers, a start and inputs) and, for chosen ticks, the values
worked out by hand from this document, with the working: phases and poses of a ping-pong mover, a rider carried
exactly, the tick a mover stops at a player and the phase it stops at, a rider jumping off mid-motion, a parked mover
equal to a static box, and the tunnelling bound's refusal on either side of it. Both implementations are held to
those values (not to each other's output), and then to each other, every tick's snapshot and hash.
