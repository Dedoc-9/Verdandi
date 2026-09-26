# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `combat` (URDRCMB1) — the certified damage-resolution law.

The law under test is `resolve(attack, defense) = max(0, attack - defense)` over 0..STAT_MAX. The
neutral-ruler discipline is the point of this suite: the oracle the tests check against is written HERE,
independently of `combat`, and a corpus of frozen literal tuples shares no code with `resolve` at all —
so a `+1`, a `<`-vs-`<=`, or a floor-clamp mutation is caught by a ruler that could not have inherited
the same bug.

Every test can go red (the mutants prove it); the plants bite before any golden pins."""
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

import combat as C                                                        # noqa: E402


# --- oracles written HERE, sharing no code with combat.resolve --------------------------------------------
def _loop_oracle(a, d):
    """Saturating decrement: start at `a`, step down `d` times but never below zero. A THIRD derivation of
    saturating subtraction (a loop), independent of both `resolve` (max) and combat._oracle (min)."""
    x = a
    for _ in range(d):
        if x > 0:
            x -= 1
    return x


#: FROZEN LITERAL expectations — the strongest neutral ruler: constants, no algorithm.
FROZEN = (
    (0, 0, 0), (1, 0, 1), (5, 5, 0), (6, 5, 1), (5, 6, 0), (10, 3, 7),
    (0, 5, 0), (7, 0, 7), (255, 0, 255), (0, 255, 0), (255, 255, 0), (255, 254, 1),
    (200, 199, 1), (100, 100, 0), (100, 101, 0),
)


class TheFormula(unittest.TestCase):
    def test_resolve_matches_an_independently_written_loop_oracle(self):
        # a sampled square (full 256x256 is exercised by the module's own exhaustive law)
        vals = list(range(0, 256, 7)) + [254, 255]
        for a in vals:
            for d in vals:
                with self.subTest(a=a, d=d):
                    self.assertEqual(C.resolve(a, d), _loop_oracle(a, d))

    def test_the_frozen_literal_tuples_match(self):
        for a, d, dmg in FROZEN:
            with self.subTest(a=a, d=d):
                self.assertEqual(C.resolve(a, d), dmg)

    def test_the_law_is_not_constant(self):
        self.assertNotEqual(C.resolve(10, 3), C.resolve(5, 5))
        self.assertTrue(C.two_inputs_produce_different_results())


class TheBoundaries(unittest.TestCase):
    def test_equal_stats_deal_zero(self):
        for x in (0, 1, 5, 100, 255):
            self.assertEqual(C.resolve(x, x), 0)

    def test_one_over_deals_exactly_one(self):
        for d in (0, 4, 99, 254):
            self.assertEqual(C.resolve(d + 1, d), 1)

    def test_one_under_is_clamped_to_zero(self):
        for a in (0, 4, 99, 254):
            self.assertEqual(C.resolve(a, a + 1), 0)

    def test_the_floor_is_zero_not_one(self):
        # a fully-mitigated attack deals nothing — no minimum-damage rule
        self.assertEqual(C.resolve(3, 10), 0)
        self.assertTrue(C.a_fully_mitigated_attack_is_exactly_zero())

    def test_overcoming_is_exactly_the_difference(self):
        self.assertTrue(C.an_overcoming_attack_is_exactly_the_difference())


class TheMitigationShape(unittest.TestCase):
    def test_exhaustive_agreement_with_the_min_oracle(self):
        self.assertTrue(C.resolve_matches_the_independent_oracle())

    def test_frozen_boundary_law(self):
        self.assertTrue(C.the_frozen_boundary_tuples_match())

    def test_damage_is_monotone(self):
        self.assertTrue(C.damage_is_monotone())
        # spot-check the direction directly against the independent loop oracle
        self.assertGreaterEqual(_loop_oracle(50, 10), _loop_oracle(50, 20))
        self.assertGreaterEqual(_loop_oracle(60, 10), _loop_oracle(50, 10))


class ThePlantedMutationReddens(unittest.TestCase):
    """The falsifier is non-vacuous: each planted mutant disagrees with an INDEPENDENT oracle."""

    def test_floor_zero_to_one_reddens(self):
        mutant = lambda a, d: max(1, a - d)
        self.assertTrue(any(mutant(a, d) != _loop_oracle(a, d)
                            for a in range(256) for d in range(256)))
        self.assertNotEqual(mutant(5, 5), _loop_oracle(5, 5))    # a concrete witness

    def test_off_by_one_reddens(self):
        mutant = lambda a, d: max(0, a - d + 1)
        self.assertNotEqual(mutant(5, 5), _loop_oracle(5, 5))
        self.assertNotEqual(mutant(0, 0), _loop_oracle(0, 0))

    def test_dropped_tie_damage_reddens(self):
        mutant = lambda a, d: (a - d) if a - d > 1 else 0
        self.assertNotEqual(mutant(1, 0), _loop_oracle(1, 0))    # a=d+1 should be 1, mutant gives 0

    def test_the_module_confirms_all_mutants_are_caught(self):
        self.assertTrue(C.a_planted_mutation_reddens())


class TheRefuseDomain(unittest.TestCase):
    def test_malformed_attack_refuses_typed(self):
        for bad in (-1, C.STAT_MAX + 1, 1.0, "5", None, True):
            with self.subTest(attack=bad):
                with self.assertRaises(C.CombatError) as cm:
                    C.resolve(bad, 0)
                self.assertEqual(cm.exception.code, "COMBAT-REFUSE")

    def test_malformed_defense_refuses_typed(self):
        for bad in (-1, C.STAT_MAX + 1, 1.0, "5", None, False):
            with self.subTest(defense=bad):
                with self.assertRaises(C.CombatError) as cm:
                    C.resolve(0, bad)
                self.assertEqual(cm.exception.code, "COMBAT-REFUSE")

    def test_bool_is_not_a_stat(self):
        # bool is an int subclass; it must not sneak through as 0/1
        with self.assertRaises(C.CombatError):
            C.resolve(True, 0)
        with self.assertRaises(C.CombatError):
            C.resolve(0, False)

    def test_refuse_is_total(self):
        self.assertEqual(C.refuse_is_total(), (True, True))


class DeterminismAndLayer(unittest.TestCase):
    def test_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import combat as C; "
                "print('|'.join(C.scene_result(n) for n in C.SCENES))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)

    def test_imports_are_stdlib_only_and_no_game_modules(self):
        top = self._mod_scope_imports("combat.py")
        self.assertEqual(top, set(C.ALLOWED_IMPORTS))
        self.assertEqual(top, {"hashlib", "os"})
        # the only thing beyond the declared substrate is `ast`, lazily imported in the leaf law
        self.assertLessEqual(self._imports("combat.py") - top, {"ast"})
        for game in ("entity", "move", "rngstream", "gamegen", "descent"):
            self.assertNotIn(game, self._imports("combat.py"))

    def test_the_module_reports_itself_a_stdlib_leaf(self):
        self.assertTrue(C.the_module_is_a_stdlib_leaf())

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(C.LAYER, "CORE")
        self.assertIn("canonical game state", C.D24_ANSWER)

    def test_no_result_representation_is_claimed_yet(self):
        # the honest minimality: a damage integer has no canonical byte form yet
        self.assertFalse(hasattr(C, "damage_bytes"))
        self.assertFalse(hasattr(C, "damage_digest"))

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


class TheDeclaredDomain(unittest.TestCase):
    def test_stat_max_is_a_byte(self):
        self.assertEqual(C.STAT_MAX, 255)

    def test_the_grid_and_boundary_are_within_domain(self):
        for x in C.GRID:
            self.assertTrue(0 <= x <= C.STAT_MAX)
        for a, d, _dmg in C.BOUNDARY:
            self.assertTrue(0 <= a <= C.STAT_MAX and 0 <= d <= C.STAT_MAX)


class TheRecord(unittest.TestCase):
    def test_scenes_match_their_goldens(self):
        for n in C.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(C.scene_result(n), C.golden(n))
        self.assertEqual(C.combat_digest(), C.golden("combat"))
        self.assertTrue(C.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(C.an_unpinned_name_refuses())
        with self.assertRaises(C.CombatError):
            C.golden("wishful")


if __name__ == "__main__":
    unittest.main()
