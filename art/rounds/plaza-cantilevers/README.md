<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# Round: "make the cantilevers more imposing"

The third round of DIRECTOR-0 on the plaza-night brief: the owner's example of a natural-language visual edit for the
native slice. It answers the art note left after the first round's candidate C: the heavier slabs need light beneath
them to read at night. The candidates use the exporter's canopy options `deep`, `ribs` and `lit`, recorded in the
ledger by a rebase (#14), and were written at head `cac46b5c8e28`. The verdicts are the ledger's (events 18 to 20),
not this page's.

| file | the idea | scope | verdict at that head |
|---|---|---|---|
| `A.intent` | weight: every slab 1.2 m deep, with downstand ribs 0.8 m deep every two cells | `plaza/canopy/*` | CLEAN |
| `B.intent` | light: the slabs unchanged in form, with warm downlights set into their undersides every other cell | `plaza/canopy/*` | CLEAN |
| `C.intent` | both: deep ribbed slabs, the downlights between the ribs | `plaza/canopy/*` | CLEAN |
| `D.intent` | the owner's note: the nearest (north) slab alone, down from 7.0 to 4.6 m and 2.2 m deep, dark beneath but for a narrow row of warm fixtures along its plaza edge | `plaza/canopy/*` | CLEAN (#22) |
| `E.intent` | D's north slab, with the far slabs as in C | `plaza/canopy/*` | CLEAN (#23) |

Every candidate changes the canopies and nothing else: the play boxes are the same 87, and the layout is untouched.
Seen in the native renderer, A's ribs are lost in the dark, and B's light makes the soffits read. C reads as a
structure. Nothing here is admitted until the owner chooses.

D and E answer the owner's note on the round's sheet (2026-10-11): *"Make the nearest cantilever lower and larger in
frame, then keep its underside mostly dark with a narrow row of warm fixtures along the edge."* They use the canopy's
`edgelit` option, recorded by a rebase (#21), and were written at head `1ff8e5e8f6be`. The ledger keeps A, B and C's
verdicts at `cac46b5c8e28`; played through `art/play.py`, they are evaluated at the head they meet and marked
HEAD-MOVED. The slab stays over its two rows: over a third,
the plaza's pole lamps would stand under it and light the underside. To walk under them:

```
python art/play.py plaza-night --intent art/rounds/plaza-cantilevers/C.intent --intent art/rounds/plaza-cantilevers/D.intent --intent art/rounds/plaza-cantilevers/E.intent
```
