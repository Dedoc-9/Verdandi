# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `heirloom` (URDRHEI1) — the certified generational-growth law.

The law under test is `heir(q) = q + (q * NUM) // DEN` over the non-negative integers. The neutral-ruler
discipline is the point: the oracles checked against are written HERE, independently of `heirloom` — a
loop that accumulates the fractional growth, and a corpus of frozen literal tuples — so a shrink, a
replace-not-grow, or an off-by-one is caught by a ruler that could not have inherited the same bug.

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

import heirloom as H                                                      # noqa: E402


# --- oracles written HERE, sharing no code with heirloom.heir ---------------------------------------------
def _loop_oracle(q):
    """Accumulate the growth by repeated fractional accrual: add 1 to a running growth for each whole DEN
    that fits into q*NUM. A different algorithm from `heir` (add-after-floor) and from the module's own
    combined-numerator oracle."""
    accrued = q * H.NUM
    grown = 0
    while accrued >= H.DEN:
        accrued -= H.DEN
        grown += 1
    return q + grown


#: FROZEN LITERAL expectations for NUM=1, DEN=8 — the strongest neutral ruler: constants, no algorithm.
FROZEN = (
    (0, 0), (1, 1), (7, 7), (8, 9), (9, 10), (15, 16), (16, 18), (23, 25),
    (24, 27), (64, 72), (100, 112), (128, 144), (200, 225), (255, 286),
)


class TheLaw(unittest.TestCase):
    def test_heir_matches_an_independent_loop_oracle(self):
        vals = list(range(0, 256, 5)) + [7, 8, 254, 255]
        for q in vals:
            with self.subTest(q=q):
                self.assertEqual(H.heir(q), _loop_oracle(q))

    def test_the_frozen_literal_tuples_match(self):
        for q, qp in FROZEN:
            with self.subTest(q=q):
                self.assertEqual(H.heir(q), qp)

    def test_the_law_is_not_constant(self):
        self.assertNotEqual(H.heir(64), H.heir(200))
        self.assertTrue(H.two_inputs_produce_different_results())

    def test_the_fraction_is_one_eighth(self):
        self.assertEqual((H.NUM, H.DEN), (1, 8))


class TheDirection(unittest.TestCase):
    def test_growth_never_shrinks(self):
        self.assertTrue(H.growth_never_shrinks())
        for q in (0, 1, 8, 100, 255):
            self.assertGreaterEqual(H.heir(q), q)

    def test_the_generational_sequence_is_monotone(self):
        self.assertTrue(H.the_generational_sequence_is_monotone())
        seq = H.generations(8, 20)
        self.assertTrue(all(seq[i + 1] >= seq[i] for i in range(len(seq) - 1)))
        # from a positive baseline above the threshold it is STRICTLY increasing
        self.assertTrue(all(seq[i + 1] > seq[i] for i in range(len(seq) - 1)))

    def test_strict_above_threshold_and_zero_below(self):
        self.assertTrue(H.growth_is_strict_above_the_threshold())
        # DEN/NUM = 8: q in 0..7 do not grow; q >= 8 grow strictly
        for q in range(0, 8):
            self.assertEqual(H.heir(q), q)
        for q in range(8, 40):
            self.assertGreater(H.heir(q), q)

    def test_generations_unbounded(self):
        # growth is not capped by the corpus bound; the quantity grows past it
        seq = H.generations(255, 6)
        self.assertGreater(seq[-1], H.CORPUS_MAX)


class ThePlantedMutationReddens(unittest.TestCase):
    """The falsifier is non-vacuous: each planted mutant disagrees with the INDEPENDENT loop oracle."""

    def test_shrink_reddens(self):
        mutant = lambda q: q - (q * H.NUM) // H.DEN
        self.assertTrue(any(mutant(q) != _loop_oracle(q) for q in range(256)))
        self.assertNotEqual(mutant(8), _loop_oracle(8))

    def test_replace_not_grow_reddens(self):
        mutant = lambda q: (q * H.NUM) // H.DEN
        self.assertNotEqual(mutant(1), _loop_oracle(1))

    def test_off_by_one_reddens(self):
        mutant = lambda q: q + (q * H.NUM + 1) // H.DEN
        self.assertTrue(any(mutant(q) != _loop_oracle(q) for q in range(256)))

    def test_min_growth_one_is_a_different_law(self):
        # the DEFERRED minimum-growth rule: it reddens against the current law at the zero-growth region
        mutant = lambda q: q + max(1, (q * H.NUM) // H.DEN)
        self.assertNotEqual(mutant(0), _loop_oracle(0))

    def test_the_module_confirms_all_mutants_are_caught(self):
        self.assertTrue(H.a_planted_mutation_reddens())


class TheRefuseDomain(unittest.TestCase):
    def test_malformed_quantity_refuses_typed(self):
        for bad in (-1, 1.0, "5", None, True, -8):
            with self.subTest(q=bad):
                with self.assertRaises(H.HeirloomError) as cm:
                    H.heir(bad)
                self.assertEqual(cm.exception.code, "HEIRLOOM-REFUSE")

    def test_bool_is_not_a_quantity(self):
        with self.assertRaises(H.HeirloomError):
            H.heir(True)
        with self.assertRaises(H.HeirloomError):
            H.heir(False)

    def test_generations_refuses_bad_count(self):
        for bad in (-1, 1.0, "3", None, True):
            with self.subTest(n=bad):
                with self.assertRaises(H.HeirloomError):
                    H.generations(10, bad)

    def test_refuse_is_total(self):
        self.assertEqual(H.refuse_is_total(), (True, True))


class DeterminismAndLayer(unittest.TestCase):
    def test_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import heirloom as H; "
                "print('|'.join(H.scene_result(n) for n in H.SCENES))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)

    def test_imports_are_stdlib_only_and_no_arc_modules(self):
        top = self._mod_scope_imports("heirloom.py")
        self.assertEqual(top, set(H.ALLOWED_IMPORTS))
        self.assertEqual(top, {"hashlib", "os"})
        self.assertLessEqual(self._imports("heirloom.py") - top, {"ast"})
        for arc in ("entity", "persist", "rngstream", "move", "gamegen"):
            self.assertNotIn(arc, self._imports("heirloom.py"))

    def test_the_module_reports_itself_a_stdlib_leaf(self):
        self.assertTrue(H.the_module_is_a_stdlib_leaf())

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(H.LAYER, "CORE")
        self.assertIn("canonical game state", H.D24_ANSWER)

    def test_no_result_representation_is_claimed_yet(self):
        self.assertFalse(hasattr(H, "quantity_bytes"))
        self.assertFalse(hasattr(H, "heir_digest"))

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


class TheRecord(unittest.TestCase):
    def test_scenes_match_their_goldens(self):
        for n in H.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(H.scene_result(n), H.golden(n))
        self.assertEqual(H.heirloom_digest(), H.golden("heirloom"))
        self.assertTrue(H.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(H.an_unpinned_name_refuses())
        with self.assertRaises(H.HeirloomError):
            H.golden("wishful")


if __name__ == "__main__":
    unittest.main()
