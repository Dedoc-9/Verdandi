<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# The self-tests' round

`art/director.py`'s self-test, crash test and race test play a round of candidates through the whole lifecycle
(evaluate, refuse, admit, a head that moves, re-evaluation, undo). Until 0229 they played the first round itself,
[`art/rounds/plaza-imposing/`](../../rounds/plaza-imposing/), the owner's round of 2026-10-10. Its base no longer passes
the checks: the base brief hangs its two cantilevers at 5.2 m over the plaza's north and south rows, and over the 2.6 m
covers at 20,11, 27,11, 20,20 and 27,20 a player stands (the graybox's simulation climbs a jump's apex and a step,
1.775 m, from the plaza's 1 m steps) and raises a head to 5.625 m. The reach ceiling before 0229 counted a climb of the
apex alone and never reached those covers; REACH-1 (art/README.md) puts the ceiling there at 5.875 m, and every
candidate that keeps those slabs is refused for them (MEASURED, 0229, at today's exporter: A and B, CLEAN before,
REFUSED CHECK-FAILED; D, LEAKAGE before, REFUSED CHECK-FAILED and SCOPE-LEAK; C, which raises the slabs to 7 m, CLEAN;
E and F REFUSED, as before). Over this base: A, B and C CLEAN, D LEAKAGE, E and F REFUSED, the round's own verdicts.

So the self-tests play the same round over a base with those two slabs at 6.0 m, and nothing else changed:
`base/plaza-night.art` is the round's base with the two lines `canopy plaza concrete 5.2 19,10 28,11` and
`canopy plaza concrete 5.2 19,20 28,21` at 6.0 (art `9f0d7a145ace`, the round's `8ce1c27f32a1`); `base/tactical.design`
and `base/tactical.layout` are the round's, byte for byte; each intent is the round's, byte for byte, but the base's
`art_sha256`. The round as the owner played it, its verdicts and its record stay in `art/rounds/plaza-imposing/` and in
his ledger, unchanged. A change to these files changes what the self-tests expect; make it with them.
