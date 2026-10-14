# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
#
# graybox/translate_probe.py — a measurement, not a check (off the gate, off every self-test): are rules 1's ticks
# translation-invariant? Prep for the owner's open-world proposal of 2026-10-14 (region-indexed coordinates, a world
# rebased as the player travels), whose determinism argument rests on moving the origin changing nothing.
#
#   python graybox/translate_probe.py [MAP]
#
# The map is moved by X0 metres along x and z (a whole number of cells, so every cell, spawn, target and the objective
# keep their places relative to each other), and the stress run (rules 1's inputs made from integers) is played from
# spawn A in both. Per tick, the moved run's position less X0 (exact: the two are within a factor of two, Sterbenz)
# is set against the unmoved run's, and the first tick at which a cell, the footing or a hit differs is found. It uses
# tick_ref.py's rules 1 as they are; it writes nothing. What it does not show: anything about another map, another run,
# rules 2, or an engine (it is Python's arithmetic, which RULES-1.md makes every engine's).

import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import level  # noqa: E402
import tick_ref as T  # noqa: E402


class Moved(T.World):
    """The world moved by K cells along x and z."""

    def __init__(self, conv, K):
        T.World.__init__(self, conv)
        self.K = K
        self.spawns = {k: (sx + K, sz + K, y) for k, (sx, sz, y) in self.spawns.items()}
        self.target_cells = [(i, x + K, z + K) for i, x, z in self.target_cells]
        if self.objective:
            a, b, c, d = self.objective
            self.objective = (a + K, b + K, c + K, d + K)

    def top(self, i, j):
        return T.World.top(self, i - self.K, j - self.K)


def run(world, inputs):
    s = T.State.new(world, "A")
    out = []
    for inp in inputs:
        T.tick(world, s, dict(inp))
        out.append((s.x, s.z, s.feet, s.on_ground, s.score))
    return out


def main(argv):
    name = argv[0] if argv else "tactical"
    conv = level.convert(name)
    cell = conv["collision"]["cell"]
    inputs = T.stress_inputs(3600)
    base = run(T.World(conv), inputs)
    print("TRANSLATE-PROBE  map %s, the stress run (%d ticks) from spawn A, the world moved by X0 along x and z" % (name, len(inputs)))
    for k in (7, 10, 14, 17, 20, 23):
        X0 = float(2 ** k)
        moved = run(Moved(conv, int(X0 / cell)), inputs)
        first, worst, discrete = None, 0.0, None
        for t, (a, b) in enumerate(zip(base, moved)):
            gap = max(abs((b[0] - X0) - a[0]), abs((b[1] - X0) - a[1]), abs(b[2] - a[2]))
            if gap and first is None:
                first = t + 1
            worst = max(worst, gap)
            if discrete is None and (b[3] != a[3] or b[4] != a[4] or math.floor(a[0] / cell) != math.floor((b[0] - X0) / cell)
                                     or math.floor(a[1] / cell) != math.floor((b[1] - X0) / cell)):
                discrete = t + 1
        print("X0 = 2^%d m (%g km): doubles there %.3g m apart; the runs apart from tick %s; the widest gap %.3g m; "
              "a cell, the footing or a hit different from tick %s" % (k, X0 / 1000, math.ulp(X0 + 50), first, worst, discrete or "never"))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
