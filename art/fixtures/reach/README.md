<!-- SPDX-License-Identifier: AGPL-3.0-only -->
# REACH-1's witness

`art/check.py` plays this world after the briefs (`== reach-witness`), as REACH-1's regression (0257). It is not a
brief: nothing exports it but the checks, and it has no reference and no ledger.

- `maps/reachpair.gbx`, `maps/reachpair.layout`: a grid of 8 by 3 cells of 2 m. A platform over cells x 0 and 1, every
  row, its top 3.8125 m and its east edge at x = 4 m; open cells at 0 elsewhere; spawn A over cell 1,1, facing +x.
- `reachpair.art`: the world dressed with one static box (a mover of speed 0, the least travel the grammar admits), its
  top 2.0 m, from x = 10.3984375 m to 13 m, across the whole width.

The box's gap, 6.3984375 m, is the farthest on the 1/256 m grid that the tick reaches from the platform's edge. The
checks derive it from the rules and hold the fixture to it: 2r + 114 ticks of walking = 6.4 m, the last tick at whose
start the box's top is still within the step of the feet. Before 0257, REACH-1 timed the flight on the parabola, whose
limit is 6.393745 m, and so refused the box. Yet the tick lands on it at tick 114, and a jump from it raises a head to
4.995833 m over cell 5,1, under a ceiling of 4.2431 m (the independent reproduction of 2026-10-19).

The rows:
- the gap is the rules' farthest;
- the tick lands on the box;
- both twins count it and keep the head from it under the ceiling less the margin;
- an exact tie (a box 5.25 m off and 0.09375 m higher, 2r + 91 steps exactly) is counted by both twins, the contract's
  conservative count, whatever the tick's own verdict there;
- a plant: the pair test before 0257, the parabola's, misses the box.

Not here: targets, moving movers, approaches off the axis, Linux.
