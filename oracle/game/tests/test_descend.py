# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `descend` (URDRDEP1) — the authoritative depth transition.

  THE PRECONDITION IS THE DOWN-STAIRS: descend refuses (DESCEND-REFUSE) unless the supplied position is
    the level's unique down endpoint; a malformed level surfaces `descent`'s DESCENT-REFUSE, not ours.
  THE ARRIVAL IS THE SUCCESSOR'S SPAWN, consumed not re-proved: pos' == descent.endpoints(level').up ==
    move.spawn(level'); the successor level is gamegen's own, one deeper, same seed.
  THE CEILING IS gamegen's, INHERITED: at DEPTH_MAX the descent refuses GAMEGEN-REFUSE before generating
    a successor and without mutating the input, and descend names no DEPTH_MAX of its own.
  RNG IS UNTOUCHED: descend imports no rngstream (declared substrate and full AST).

Every test can go red (L5); the plants bite before any golden pins (L15)."""
import ast
import io
import os
import subprocess
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = os.path.join(ROOT, "tools", "terrain")
if _T not in sys.path:
    sys.path.insert(0, _T)

import descend as X                                                       # noqa: E402
import gamegen as G                                                      # noqa: E402
import descent as D                                                      # noqa: E402
import move as M                                                         # noqa: E402


def _down(seed, depth):
    lv = G.generate(seed, depth)
    return lv, D.endpoints(lv)[1]


class ThePrecondition(unittest.TestCase):
    def test_descend_from_the_down_stairs_succeeds(self):
        lv, down = _down(0, 1)
        level_next, pos_next = X.descend(lv, down)
        self.assertEqual(level_next.depth, 2)
        self.assertEqual(pos_next, D.endpoints(level_next)[0])

    def test_descending_off_the_down_stairs_refuses_typed(self):
        lv = G.generate(12345, 1)
        up, down = D.endpoints(lv)
        floor = next((x, y) for y in range(lv.h) for x in range(lv.w)
                     if lv.cells[y][x:x + 1] == G.FLOOR)
        for bad in (up, floor, (0, 0)):
            with self.subTest(pos=bad):
                with self.assertRaises(X.DescendError) as cm:
                    X.descend(lv, bad)
                self.assertEqual(cm.exception.code, "DESCEND-REFUSE")

    def test_a_malformed_level_is_descents_refusal_not_ours(self):
        self.assertTrue(X.a_malformed_level_is_descents_refusal_not_ours())
        lv, down = _down(0, 1)
        no_down = lv.replaced(cells=tuple(bytes(bytearray(r).replace(G.DOWN, G.FLOOR))
                                          for r in lv.cells))
        with self.assertRaises(D.DescentError) as cm:
            X.descend(no_down, down)
        self.assertEqual(cm.exception.code, "DESCENT-REFUSE")


class TheArrivalIsTheSpawn(unittest.TestCase):
    def test_successor_position_equals_move_spawn(self):
        for s, d in [(s, d) for s, d in G.CORPUS if d < G.DEPTH_MAX]:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(X.the_successor_position_is_the_authoritative_spawn(s, d))
                lv, down = _down(s, d)
                level_next, pos_next = X.descend(lv, down)
                self.assertEqual(pos_next, M.spawn(level_next))
                self.assertTrue(D.traversable(level_next, *pos_next))

    def test_successor_reproduces_gamegen_and_preserves_seed(self):
        for s, d in [(s, d) for s, d in G.CORPUS if d < G.DEPTH_MAX]:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(X.the_successor_reproduces_gamegen(s, d))
                lv, down = _down(s, d)
                level_next, _p = X.descend(lv, down)
                self.assertEqual(G.level_digest(level_next), G.digest_of(s, d + 1))
                self.assertEqual(level_next.seed, s)
                self.assertEqual(level_next.depth, d + 1)

    def test_successor_identity_is_the_one_move_vocabulary(self):
        lv, down = _down(0, 1)
        level_next, pos_next = X.descend(lv, down)
        self.assertEqual(X.successor_state_digest(lv, down), M.state_digest(level_next, pos_next))


class TheCeiling(unittest.TestCase):
    def test_at_depth_max_refuses_gamegen_without_generating_or_mutating(self):
        refused, unchanged, no_literal = X.the_ceiling_refuses_without_generating(7)
        self.assertTrue(refused, "the ceiling did not refuse with GAMEGEN-REFUSE")
        self.assertTrue(unchanged, "the input level was mutated by a refused descent")
        self.assertTrue(no_literal, "descend.py names a DEPTH_MAX literal — a second depth law")

    def test_the_ceiling_code_is_gamegens_not_ours(self):
        lv, down = _down(7, G.DEPTH_MAX)
        with self.assertRaises(G.GamegenError) as cm:
            X.descend(lv, down)
        self.assertEqual(cm.exception.code, "GAMEGEN-REFUSE")

    def test_descend_names_no_depth_max(self):
        """STRUCTURAL: no second depth law. descend references gamegen's DEPTH_MAX as an attribute
        (`_G.DEPTH_MAX`) but defines no bare `DEPTH_MAX` name of its own."""
        with io.open(os.path.join(_T, "descend.py"), encoding="utf-8") as fh:
            names = {n.id for n in ast.walk(ast.parse(fh.read())) if isinstance(n, ast.Name)}
        self.assertNotIn("DEPTH_MAX", names)

    def test_the_positive_boundary_witness_descends_to_depth_max(self):
        self.assertTrue(X.the_boundary_below_the_ceiling_descends())
        lv, down = _down(7, G.DEPTH_MAX - 1)
        level_next, _p = X.descend(lv, down)
        self.assertEqual(level_next.depth, G.DEPTH_MAX)
        self.assertEqual(G.level_digest(level_next), G.digest_of(7, G.DEPTH_MAX))


class RngIsUntouched(unittest.TestCase):
    def test_descend_imports_no_rngstream(self):
        self.assertTrue(X.this_module_touches_no_rng())
        self.assertNotIn("rngstream", set(X.ALLOWED_IMPORTS))
        self.assertNotIn("rngstream", self._imports("descend.py"))

    def test_descend_takes_and_returns_no_stream(self):
        """The independence is structural: descend's signature carries no stream, so it cannot advance
        one. A descent returns exactly (level', pos') — a (level, entity) successor, nothing else."""
        lv, down = _down(0, 1)
        out = X.descend(lv, down)
        self.assertEqual(len(out), 2)
        self.assertIsInstance(out[0], G.Level)
        self.assertIsInstance(out[1], tuple)

    def _imports(self, name):
        with io.open(os.path.join(_T, name), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        return found


class DeterminismAndLayer(unittest.TestCase):
    def test_the_transition_is_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import descend as X; "
                "print('|'.join(X.scene_result(n) for n in X.SCENES))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)

    def test_imports_are_the_declared_substrate_at_module_scope(self):
        top = self._mod_scope_imports("descend.py")
        self.assertEqual(top, set(X.ALLOWED_IMPORTS))
        self.assertEqual(top, {"hashlib", "os", "gamegen", "descent"})

    def test_move_is_reached_only_lazily_and_the_dependency_runs_one_way(self):
        top = self._mod_scope_imports("descend.py")
        allimp = self._all_imports("descend.py")
        self.assertIn("move", allimp)          # for the spawn-equivalence law and the state vocabulary
        self.assertNotIn("move", top)          # but not at module scope
        for upstream in ("gamegen.py", "descent.py", "move.py"):
            self.assertNotIn("descend", self._all_imports(upstream))

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(X.LAYER, "CORE")
        self.assertIn("canonical game state", X.D24_ANSWER)

    def _all_imports(self, name):
        with io.open(os.path.join(_T, name), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        return found

    def _mod_scope_imports(self, name):
        with io.open(os.path.join(_T, name), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        return found


class TheRecord(unittest.TestCase):
    def test_scenes_match_their_goldens(self):
        for n in X.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(X.scene_result(n), X.golden(n))
        self.assertEqual(X.descend_digest(), X.golden("descend"))
        self.assertTrue(X.emitted_matches_pinned())

    def test_refuse_is_total(self):
        self.assertEqual(X.refuse_is_total(), (True, True, True))

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(X.an_unpinned_name_refuses())
        with self.assertRaises(X.DescendError):
            X.golden("wishful")


if __name__ == "__main__":
    unittest.main()
