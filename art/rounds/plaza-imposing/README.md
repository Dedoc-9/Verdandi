<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Round: "make the plaza more imposing"

The first round of DIRECTOR-0 on the plaza-night brief. The candidates were written by the model as art director,
each at the head the ledger's genesis records. Each also exercises one part of the protocol, so the round tests the
protocol rather than only illustrating it. The verdicts are the ledger's (`art/ledger/plaza-night.ledger`, events 1
to 8), not this page's.

| file | the idea | what it exercises | verdict at the first head |
|---|---|---|---|
| `A.intent` | monumental towers: the plaza's ring at 16–30 m, in a concrete of its own | a revision of the look alone, scoped exactly | CLEAN |
| `B.intent` | compression, then release: the north flank closed to a one-cell slot, lit hard over every cell | a layout change, through the design tool, under a layout grant | CLEAN |
| `C.intent` | heavier cantilevers: two slabs at 7 m, near-black, and a third over the west edge | a candidate that goes stale once A or B is admitted, and must be re-evaluated | CLEAN |
| `D.intent` | colder, harder concrete and brighter magenta, "for the plaza" | the reference graph: shared materials reach the bases' towers, every wall and the mid lanes' neon | LEAKAGE |
| `E.intent` | a fortress: the south flank sealed | an out-of-scope layout change: cells outside its grant, and a probe that must stay open | REFUSED |
| `F.intent` | a monolith hovering over the platform at 3.6 m | the seatbelt: dressing where a player's head can be | REFUSED |
| `G-unknown-version.intent` | A again, as version "1" | an unknown version is refused, never translated | refused on input |
| `H-malformed.intent` | A again, with a number for its version | malformed input | refused on input |

A, B and C can all be admitted, in any order. After the first, the others meet a moved head and are re-evaluated
before admission (`python art/director.py reevaluate`).
