<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The graybox's rules, version 3: solid walls, standing targets, push

Rules 3 are [rules 2](RULES-2.md) with four changes: a **wall** holds the body at any height; a standing **target has a
top** a player can stand on; a target that would stand again while a body is in its column **waits**; and a mover may
have the policy **push**, moving a player in its way with it. Everything rules 2 say holds under rules 3 except where
this document says otherwise. Like rules 2, it is the specification two implementations are written from, `web/sim.js`
(`GrayboxSim.withRules(3)`) and `tick_ref.py` (`rules3`); where they disagree, one of them is wrong. Rules 1 and 2 are
unchanged by it, byte for byte (their tables, identities and hashes held again after the change).

From the owner's report of 2026-10-14, playing harbor-lift under rules 2: from the lift he jumped onto the ledge toward
the centre and could *"walk through the wall up there"*; on a dummy he got *"stuck into it instead of collision
keeping me on top of it"*, freed only by shooting it down; and the sliding deck *"doesn't move my would be character if
i get in the way like when lifted"*. Measured in the container from his report (graybox/web/sim.js, rules 2 and 1):

| what he saw | what the rules said | measured |
|---|---|---|
| walking through the wall | rules 1 and 2 know no wall: a wall is a cell 4 m high, and a cell no more than a step (0.55 m) above the feet can be stepped onto. A jump rises 1.225 m, so from a top of 2.6 m (a cover) or 2.5 m (the lift at its highest), 4 m is reached; the art draws the city's rock above 4 m, and the player walks inside it | tactical, rules 1, no movers: wall tops reached from the floor by way of a 1 m and a 2.6 m cover; harbor-lift, rules 2: of 1,944 jumps from the lift's top, 233 ended on a wall's top |
| stuck in a dummy | a standing target blocks a body whose feet are below its top, and has no top: a player above it walks into its column, falls into it, and every step from inside ends inside | harbor-lift: 1,045 of 15,552 tries ended inside a target |
| the deck does not move him | rules 2's one policy, stop: a mover that would enter a player holds still | as specified (RULES-2.md, *A mover's step*) |

## Arithmetic, the constants, the state

Rules 2's, unchanged. The snapshot is rules 2's.

## The world

Rules 2's, and the world's **wall height**, `wall`: the canonical map's `wall` (4 m in every map of `level.py`, whose
cells are either rock, at `wall`, or open, below it). Refused (`RULES3-WALL`) unless a number above the step and finite:
at or below the step every cell a player could step onto would be a wall.

A mover's `policy` is `"stop"` or `"push"`; any other is refused (`RULES2-MOVER`), as rules 2 refuse any but `"stop"`.
Everything else of RULES-2.md's table is unchanged, the tunnelling bound among it.

## The body

`blocked(x, z, feet)` is rules 2's, or some cell the circle of radius `radius` at `(x, z)` overlaps (strictly, as rules 1
find them) has `top ≥ wall`: **a wall holds the body at any height**, as the edge of the map always has.

`inColumn(t, x, z, feet)`: target `t` is standing, `dx·dx + dz·dz < rr·rr` with `dx = x − t.x`, `dz = z − t.z`,
`rr = radius + targetRadius`, and `feet < t.y + targetHeight`: the test rules 1's `blocked` already makes of a standing
target.

`ground(x, z, before)` is rules 2's, raised to `t.y + targetHeight` for every standing target `t` with
`dx·dx + dz·dz < rr·rr` and `t.y + targetHeight ≤ before + step`: **a standing target's top is a top like any other**,
as high as a step above `before`. A target is still a cylinder to the body and a box to a shot (rules 1); its top is not
a ceiling (a target stands on the cells, never above a head).

## One tick

Rules 2's, with two changes.

**3. The movers.** A mover's step is rules 2's but where the player is *not a rider* and `b` reaches into the body:

- policy `stop`, or any policy along `y`: nothing moves and `stopped` is true (rules 2's);
- policy `push` along `x` or `z`: the player's new place is `(x + dx, z + dz)` at the same `feet`. With this mover at
  `b` and the others where they stand, if that place is not `blocked`, then `phase = n`, `x = x + dx`, `z = z + dz`
  and `stopped` is false; otherwise nothing moves and `stopped` is true.

A rider is carried as in rules 2 whatever the policy. The pushed player keeps their place relative to the box (up to
the rounding of one addition), so is not left in it; a push into a wall, a standing target, a cell above a step or
another box holds the mover still, as stop does. Along `y` there is no push: a plate rising under a player who is not
on its top, or a box coming down onto a head, holds still.

**9. The targets.** A down target: `downFor = downFor − TICK`; when `downFor ≤ 1e-9`, if `inColumn(t, x, z, feet)` were
true of it standing (a body in its column, below its top), it **waits**: it stays down and `downFor = 0`; otherwise it
stands, `up` true and `downFor = 0`. Each later tick it tries again.

## What follows, and what does not

No tick of rules 3 ends with the body inside a box (but on its top), in a standing target's column below its top, or
over a wall's cell, from a start that is not: every way the player's place changes (walking, a rider carried, a push) is
tested by `blocked`, which holds all three; a target stands only when its column is clear; a top is landed on, never
fallen through. The stress runs W3 and W4 held it over 9,000 ticks (MEASURED, two runs). A start that puts the body
inside a target is not mended: its top is more than a step above the feet, not ground, and the player is held (R7).

Not changed: a shot meets the cells and the targets, not the movers; the player has no horizontal velocity; a mover's
vertical motion is not added to `vy`. ORT-1 moves the origin of rules 2's worlds only: a rules-3 world is refused
(`ORT-RULES`), in both implementations.

## The state's hash

Rules 2's, with the identity's first line `VERDANDI-RULES 3`, `"rules"` 3, and the world's `"wall"` in the identity
document (`"world":{…,"w":…,"wall":…}`, as the snapshot writes a number). Rules 2's identity is unchanged: a rules-2
world names no wall.

## The independent answers

`web/rules3_cases.json` holds fourteen cases worked by hand from this document, with the working, and two long runs: a pusher moving a
player and leaving him (R1), stopping when the wall is behind him (R2), at a standing target (R10); push along `y` as
stop (R3, R4); a wall holding a player 0.5 m below its top (R5); landing on a target's top (R6); a top more than a step
above the feet (R7); a target waiting for its column to clear (R8); standing on a target and shooting it from its top,
the owner's case (R9); a rider of a pusher (R11); a case none of rules 3's changes meets, the same snapshots as rules 2's
(R12); a policy refused (R13); a wall no higher than a step refused (R14); and two stress runs among three pushers
(W3, W4). Where rules 3 change what rules 2 do, the case also says what rules 2 do (`expect_rules2`), and both
implementations play it under rules 2 as well and are held to that. `tick_ref.py rules3` plants nine defects in its own
rules 3 (walls by height alone, no target top, a top at any height, a target standing at once, push as stop, push into
a wall, push along `y`, the wall left out of the identity, any wall height), each caught by a worked value.
