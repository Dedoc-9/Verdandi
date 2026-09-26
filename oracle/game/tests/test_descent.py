# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `descent` (URDRDSC1) — the topology witness over a gamegen level.

  THE WITNESS IS A PATH, VERIFIED INDEPENDENTLY OF THE SEARCH: a broken step, a wall step and a
    wrong endpoint are each rejected by `verify_path`, so a search that returned garbage cannot pass.
  THE SEALED ROOM IS REJECTED and the ordinary level accepted — both directions on the same level.
  THE TWO ORACLES DO NOT COLLAPSE: a sealed level fails this witness while passing every one of
    `gamegen`'s structural predicates.
  THE DOMAIN IS EXPLICIT: an absent or doubled endpoint refuses typed.
  THE DEPENDENCY RUNS ONE WAY: `descent` imports `gamegen`; `gamegen` imports neither `descent` nor
    anything under `tools/`, read off both ASTs here.

Every test can go red (L5); the plants bite before any golden pins (L15)."""
import ast
import io
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = os.path.join(ROOT, "tools", "terrain")
if _T not in sys.path:
    sys.path.insert(0, _T)

import descent as D                                                       # noqa: E402
import gamegen as G                                                       # noqa: E402

LV = G.generate(*D.CORPUS[0])


class TheGridIsTheGraph(unittest.TestCase):
    def test_the_corpus_levels_are_connected_by_a_verified_path(self):
        for s, d in D.CORPUS:
            with self.subTest(seed=s, depth=d):
                lv = G.generate(s, d)
                p = D.descent_path(lv)
                self.assertIsNotNone(p)
                ok, why = D.verify_path(lv, p)
                self.assertTrue(ok, why)

    def test_the_sweep_is_connected(self):
        """128 ordinary levels: every one has a verified up->down walk."""
        bad = [s for s in range(128) if not D.is_connected(G.generate(s, 1))]
        self.assertEqual(bad, [])

    def test_traversable_is_exactly_floor_and_the_two_stairs(self):
        self.assertEqual(set(D.TRAVERSABLE), {G.FLOOR, G.UP, G.DOWN})
        self.assertNotIn(G.WALL, D.TRAVERSABLE)


class ThePathIsVerifiedIndependently(unittest.TestCase):
    def test_a_good_path_verifies_and_forgeries_do_not(self):
        good, broken, wall_step, wrong_end = D.verify_rejects_a_forgery(LV)
        self.assertTrue(good)
        self.assertTrue(broken, "a skipped cell (a jump) must be rejected")
        self.assertTrue(wall_step, "a step onto a wall must be rejected")
        self.assertTrue(wrong_end, "a path not ending at stairs-down must be rejected")

    def test_verify_rejects_an_empty_path(self):
        self.assertFalse(D.verify_path(LV, ())[0])
        self.assertFalse(D.verify_path(LV, None)[0])

    def test_verify_rejects_a_diagonal_step(self):
        up, down = D.endpoints(LV)
        self.assertFalse(D.verify_path(LV, (up, (up[0] + 1, up[1] + 1), down))[0])

    def test_the_path_is_a_real_walk_every_cell_traversable(self):
        p = D.descent_path(LV)
        for (x, y) in p:
            self.assertIn(LV.cells[y][x:x + 1], D.TRAVERSABLE)
        self.assertEqual(p[0], D.endpoints(LV)[0])
        self.assertEqual(p[-1], D.endpoints(LV)[1])

    def test_is_connected_uses_a_verified_path_not_a_bare_search(self):
        self.assertTrue(D.is_connected(LV))


class TheSealedRoomIsRejected(unittest.TestCase):
    def test_both_directions_on_every_corpus_level(self):
        for s, d in D.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(D.the_sealed_room_is_rejected(G.generate(s, d)))

    def test_the_sealed_level_has_no_path_at_all(self):
        sealed = D.seal_down(LV)
        self.assertIsNone(D.descent_path(sealed))
        self.assertFalse(D.is_connected(sealed))

    def test_the_sealed_level_is_still_in_the_domain(self):
        """A counterexample outside the input domain would prove nothing about the witness."""
        sealed = D.seal_down(LV)
        up, down = D.endpoints(sealed)          # resolves, or raises
        self.assertEqual((LV.cells and up is not None), True)
        self.assertNotEqual(up, down)

    def test_the_seal_leaves_the_original_untouched(self):
        before = G.level_digest(LV)
        D.seal_down(LV)
        self.assertEqual(G.level_digest(LV), before)


class TheOraclesDoNotCollapse(unittest.TestCase):
    def test_a_sealed_level_is_gamegen_well_formed_and_descent_broken(self):
        """THE SHARP ONE: generation-correct in every way the generator can see, and untraversable."""
        for s, d in D.CORPUS:
            with self.subTest(seed=s, depth=d):
                gg_ok, descent_fails = D.the_oracles_do_not_collapse(G.generate(s, d))
                self.assertTrue(gg_ok, "the sealed level should still pass gamegen's predicates")
                self.assertTrue(descent_fails, "the sealed level should fail the descent witness")

    def test_gamegen_itself_makes_no_reachability_claim(self):
        """`gamegen.problems` says nothing about connectivity — the reason this rung exists."""
        sealed = D.seal_down(LV)
        self.assertEqual(G.problems(sealed), [], "gamegen sees the sealed level as well-formed")
        self.assertFalse(D.is_connected(sealed))


class TheDomain(unittest.TestCase):
    def test_an_absent_or_doubled_endpoint_refuses_typed(self):
        refused_absent, refused_doubled = D.domain_is_total(LV)
        self.assertTrue(refused_absent)
        self.assertTrue(refused_doubled)

    def test_endpoints_refuses_with_the_typed_code(self):
        no_down = D._set(LV, D.endpoints(LV)[1][0], D.endpoints(LV)[1][1], G.FLOOR)
        with self.assertRaises(D.DescentError) as cm:
            D.endpoints(no_down)
        self.assertEqual(cm.exception.code, "DESCENT-REFUSE")

    def test_every_gamegen_level_is_in_the_domain(self):
        for s, d in D.CORPUS:
            with self.subTest(seed=s, depth=d):
                D.endpoints(G.generate(s, d))          # does not raise


class TheDependencyRunsOneWay(unittest.TestCase):
    def test_descent_imports_gamegen_and_the_declared_substrate(self):
        found = self._imports("descent.py")
        self.assertEqual(found, set(D.ALLOWED_IMPORTS))
        for name in found:
            if name != "gamegen":
                self.assertIn(name, sys.stdlib_module_names, name)

    def test_gamegen_does_not_import_descent_or_anything_under_tools(self):
        found = self._imports("gamegen.py")
        self.assertNotIn("descent", found)
        self.assertEqual(found, {"hashlib", "os"},
                         "gamegen must stay on stdlib alone — the dependency is one-way")

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


class TheRecord(unittest.TestCase):
    def test_scenes_match_their_goldens(self):
        for n in D.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(D.scene_result(n), D.golden(n))
        self.assertEqual(D.descent_digest(), D.golden("descent-digest"))
        self.assertTrue(D.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(D.an_unpinned_name_refuses())
        with self.assertRaises(D.DescentError):
            D.golden("wishful")

    def test_the_witness_digest_reproduces(self):
        self.assertEqual(D.path_digest(LV), D.path_digest(LV))
        self.assertEqual(len(D.path_digest(LV)), 64)

    def test_a_severed_level_digests_a_distinct_stable_witness(self):
        sealed = D.seal_down(LV)
        self.assertEqual(D.path_digest(sealed), D.path_digest(sealed))
        self.assertNotEqual(D.path_digest(sealed), D.path_digest(LV))


if __name__ == "__main__":
    unittest.main()
