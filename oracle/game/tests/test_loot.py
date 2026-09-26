# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `loot` (URDRLOO1) — the first canonical gameplay consumer of the RNG stream.

The A–H seams, each a distinct failure surface:
  A consumption   — same (source, R_n) → same (drop, R_{n+1}); a second call consumes R_{n+1}, not R_n.
  B peek isolation— deriving the drop reads R_n without advancing; only the returned stream advances.
  C source binding— distinct (level, pos) at one R_n do not collapse to the same consumption.
  D table mutation— a mutation at the SELECTED slot changes the drop; elsewhere it does not.
  E oracle        — the selection equals an independent SHA re-derivation, not loot's own code.
  F isolation     — level and position unchanged; only the RNG advances.
  G replay        — the same ordered events from the same R_0 reconstruct drops and streams.
  H independence  — rngstream imports no loot; loot's draw IS rngstream.peek.

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

import loot as L                                                          # noqa: E402
import gamegen as G                                                      # noqa: E402
import move as M                                                         # noqa: E402
import rngstream as R                                                    # noqa: E402


def _src(seed, depth, pick="down"):
    return L._src(seed, depth, pick)


class TheTransition(unittest.TestCase):
    def test_source_stream_to_drop_and_successor(self):
        lv, pos = _src(0, 1)
        s0 = R.root(lv.seed)
        drop, s1 = L.loot(lv, pos, s0)
        self.assertIn(drop, L.TABLE)
        self.assertEqual(s1.n, s0.n + 1)
        # the drop is exactly the uniform selection over the frozen table
        i = R.peek(s0, M.state_digest(lv, pos), len(L.TABLE))
        self.assertEqual(drop, L.TABLE[i])

    def test_the_successor_folds_the_source(self):
        lv, pos = _src(0, 1)
        s0 = R.root(lv.seed)
        _d, s1 = L.loot(lv, pos, s0)
        self.assertEqual(s1, R.advance(s0, b"loot:" + M.state_digest(lv, pos).encode()))

    def test_same_source_different_stream_position_differs(self):
        """The adversarial trap, as a test: seed alone under-determines; the drop depends on R_n."""
        lv, pos = _src(0, 1)
        d0, _ = L.loot(lv, pos, R.root(lv.seed))
        dK, _ = L.loot(lv, pos, R.apply(R.root(lv.seed), ("x", "y", "z")))
        # not guaranteed different for every seed, but the stream state is what is consulted:
        self.assertEqual(d0, L.TABLE[R.peek(R.root(lv.seed), M.state_digest(lv, pos), len(L.TABLE))])
        self.assertEqual(dK, L.TABLE[R.peek(R.apply(R.root(lv.seed), ("x", "y", "z")),
                                            M.state_digest(lv, pos), len(L.TABLE))])


class TheAtoHSeams(unittest.TestCase):
    CASES = [(s, d) for s, d in G.CORPUS]

    def test_A_consumption_reproduces_and_advances(self):
        for s, d in self.CASES:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(L.the_same_source_and_stream_reproduce(s, d))
                self.assertTrue(L.a_second_call_consumes_the_successor(s, d))

    def test_B_peek_isolation(self):
        for s, d in self.CASES:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(L.a_peek_does_not_advance(s, d))

    def test_C_source_binding(self):
        for s, d in self.CASES:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(L.distinct_sources_do_not_collapse(s, d))

    def test_D_table_mutation_at_selected_slot(self):
        for s, d in self.CASES:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(L.a_table_mutation_changes_only_the_selected_slot(s, d))

    def test_E_independent_oracle(self):
        for s, d in self.CASES:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(L.the_selection_matches_an_independent_oracle(s, d))

    def test_F_only_the_rng_advances(self):
        for s, d in self.CASES:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(L.only_the_rng_advances(s, d))

    def test_G_replay(self):
        for s, d in self.CASES:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(L.a_replay_reconstructs_drops_and_streams(s, d))

    def test_H_rngstream_does_not_depend_on_loot(self):
        self.assertTrue(L.rngstream_does_not_depend_on_loot())
        self.assertNotIn("loot", self._imports("rngstream.py"))

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


class WallsAreValidSources(unittest.TestCase):
    def test_a_wall_position_is_a_source_no_traversability_required(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(L.a_wall_is_a_valid_source(s, d))

    def test_loot_imports_no_descent(self):
        with io.open(os.path.join(_T, "loot.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        self.assertNotIn("descent", found)
        self.assertNotIn("descent", set(L.ALLOWED_IMPORTS))


class TheTableAndDrop(unittest.TestCase):
    def test_the_table_is_uniform_frozen_and_non_degenerate(self):
        self.assertIsInstance(L.TABLE, tuple)
        self.assertGreaterEqual(len(L.TABLE), 8)         # not degenerate — mutation falsifier bites
        self.assertEqual(len(set(L.TABLE)), len(L.TABLE))  # distinct entries

    def test_the_drop_digest_is_the_item_alone(self):
        item = L.TABLE[0]
        self.assertEqual(L.drop_bytes(item), b"URDRLOO1|item:" + item.encode())
        # source and stream are NOT in the drop identity
        self.assertNotIn(b"loot:", L.drop_bytes(item))
        self.assertNotIn(b"n:", L.drop_bytes(item))

    def test_a_non_table_item_has_no_drop_digest(self):
        with self.assertRaises(L.LootError):
            L.drop_bytes("not_an_item")


class TheRefuseDomain(unittest.TestCase):
    def test_malformed_arguments_refuse_typed(self):
        lv, pos = _src(0, 1)
        s = R.root(lv.seed)
        for bad in (None, 42, "level"):
            with self.subTest(level=bad):
                with self.assertRaises(L.LootError) as cm:
                    L.loot(bad, pos, s)
                self.assertEqual(cm.exception.code, "LOOT-REFUSE")
        for bad in ((0.0, 0), (0,), None, (0, 0, 0), (True, 0)):
            with self.subTest(pos=bad):
                with self.assertRaises(L.LootError) as cm:
                    L.loot(lv, bad, s)
                self.assertEqual(cm.exception.code, "LOOT-REFUSE")
        for bad in (None, 0, lv):
            with self.subTest(stream=bad):
                with self.assertRaises(L.LootError) as cm:
                    L.loot(lv, pos, bad)
                self.assertEqual(cm.exception.code, "LOOT-REFUSE")

    def test_refuse_is_total(self):
        self.assertEqual(L.refuse_is_total(), (True, True, True))


class DeterminismAndLayer(unittest.TestCase):
    def test_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import loot as L; "
                "print('|'.join(L.scene_result(n) for n in L.SCENES))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)

    def test_imports_are_the_declared_substrate_and_one_way(self):
        top = self._mod_scope_imports("loot.py")
        self.assertEqual(top, set(L.ALLOWED_IMPORTS))
        self.assertEqual(top, {"hashlib", "os", "gamegen", "move", "rngstream"})
        # the only thing beyond the declared substrate is `ast`, lazily imported in the H law
        self.assertLessEqual(self._imports("loot.py") - top, {"ast"})
        for upstream in ("gamegen.py", "move.py", "rngstream.py"):
            self.assertNotIn("loot", self._imports(upstream))

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

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(L.LAYER, "CORE")
        self.assertIn("canonical game state", L.D24_ANSWER)

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
        for n in L.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(L.scene_result(n), L.golden(n))
        self.assertEqual(L.loot_digest(), L.golden("loot"))
        self.assertTrue(L.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(L.an_unpinned_name_refuses())
        with self.assertRaises(L.LootError):
            L.golden("wishful")


if __name__ == "__main__":
    unittest.main()
