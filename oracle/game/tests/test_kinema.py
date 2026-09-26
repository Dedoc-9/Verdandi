# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `kinema` (URDRKIN1) — the one-way observer-space refinement of an authoritative
transition. The fifteenth game-layer vertical slice, D25's cinematic membrane, and the first game-layer VIEW
module. It consumes real `enact` endpoints and `statecanon` identities and refines BETWEEN them; it never
computes the successor it observes.

The distinguishing claims, each a distinct failure surface:
  refine        — endpoints land exactly; every sample of a real move edge is contained in {A, B}.
  shapes        — MOVE -> MOVED, LOOT/BLOCKED -> FIXED, DESCEND -> LEVELCUT (a discrete cut).
  forgery       — a wall-target (Plant A) and a non-adjacent pair (Plant B) refuse KINEMA-REFUSE.
  one-way       — the full-AST direction-aware guard bites the function-local escape hatch (Plant C).
  differential  — the canonical transcript is byte-identical whether kinema is exercised or not (§14).
  sampling      — the sample count is view-only (Plant D); no CORE module imports kinema.
  arithmetic    — a one-ULP alpha perturbation is observable on the moving axis, invisible on the still one."""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = os.path.join(ROOT, "tools", "terrain")
if _T not in sys.path:
    sys.path.insert(0, _T)

import kinema as K                                                      # noqa: E402
import gamegen as G                                                     # noqa: E402
import descent as D                                                     # noqa: E402
import move as M                                                        # noqa: E402
import rngstream as R                                                   # noqa: E402
import entity as E                                                      # noqa: E402
import actionlog as A                                                   # noqa: E402
import enact as EN                                                      # noqa: E402
import savegame as SV                                                   # noqa: E402
import statecanon as SC                                                 # noqa: E402
import rerun as RP                                                      # noqa: E402
from field import ONE                                                   # noqa: E402


def _real_move(seed, depth):
    """A genuinely authoritative MOVE transition via `enact.dispatch`, with both ends identified by
    `statecanon` — exactly what KINEMA is handed."""
    lvl = G.generate(seed, depth)
    up = D.endpoints(lvl)[0]
    for c in ("N", "S", "E", "W"):
        if M.step(lvl, up, c)[0] == M.MOVED:
            s0 = (lvl, up, R.root(seed))
            log0 = A.empty()
            s1, _outcome = EN.dispatch(s0, EN.encode("MOVE", c))
            log1 = A.append(log0, EN.encode("MOVE", c))
            dn = SC.d_n(s0[0], E.at(s0[1]), s0[2], log0)
            dn1 = SC.d_n(s1[0], E.at(s1[1]), s1[2], log1)
            return s0, s1, dn, dn1
    return None


class Refine(unittest.TestCase):
    def test_endpoints_land_exactly_over_the_corpus(self):
        for s, d in K.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(K.endpoints_land_exactly(s, d))

    def test_every_sample_is_contained(self):
        for s, d in K.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(K.every_sample_is_contained(s, d))

    def test_refines_a_real_enact_transition_and_carries_the_real_witnesses(self):
        rm = _real_move(0xC0FFEE, 2)
        self.assertIsNotNone(rm)
        s0, s1, dn, dn1 = rm
        fs = K.frames(s0[0], s0[1], dn, s1[0], s1[1], dn1, 7, 6)
        self.assertEqual(K.floor_cell(fs[0].refined), s0[1])
        self.assertEqual(K.floor_cell(fs[-1].refined), s1[1])
        self.assertTrue(all(K.floor_cell(f.refined) in (s0[1], s1[1]) for f in fs))
        # the endpoint witnesses are carried VERBATIM = the real statecanon digests
        self.assertTrue(all(f.witness_n == dn and f.witness_m == dn1 for f in fs))
        self.assertTrue(all(f.source_tick == 7 for f in fs))


class Shapes(unittest.TestCase):
    def test_move_is_moved(self):
        s0, s1, _dn, _dn1 = _real_move(0xC0FFEE, 2)
        self.assertEqual(K.classify(s0[0], s0[1], s1[0], s1[1]), K.MOVED)

    def test_loot_is_a_fixed_point(self):
        lvl = G.generate(0xC0FFEE, 2)
        up = D.endpoints(lvl)[0]
        s0 = (lvl, up, R.root(0xC0FFEE))
        s1, _drop = EN.dispatch(s0, EN.encode("LOOT"))              # LOOT: position unchanged
        self.assertEqual(s1[1], s0[1])
        self.assertEqual(K.classify(s0[0], s0[1], s1[0], s1[1]), K.FIXED)

    def test_descend_is_a_level_cut_not_interpolated(self):
        lvl = G.generate(7, 2)
        down = D.endpoints(lvl)[1]
        s0 = (lvl, down, R.root(7))
        s1, _depth = EN.dispatch(s0, EN.encode("DESCEND"))          # DESCEND: the level changes
        cls = K.classify(s0[0], s0[1], s1[0], s1[1])
        self.assertEqual(cls, K.LEVELCUT)
        fs = K.frames(s0[0], s0[1], "a" * 64, s1[0], s1[1], "b" * 64, 0, 6)
        self.assertEqual(len(fs), 2)                                 # a discrete cut, no intermediate
        self.assertTrue(all(f.cls == K.LEVELCUT for f in fs))


class Forgery(unittest.TestCase):
    def test_wall_crossing_refuses_plant_a(self):
        for s, d in K.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(K.a_forged_wall_crossing_refuses(s, d))

    def test_non_adjacent_refuses_plant_b(self):
        for s, d in K.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(K.a_forged_nonadjacent_refuses(s, d))

    def test_a_real_wall_target_refuses_typed(self):
        lvl = G.generate(0, 1)
        floor, wall = K._wall_edge(lvl)
        self.assertIsNotNone(wall, "a generated level should have a floor cell bordering a wall")
        self.assertTrue(D.traversable(lvl, floor[0], floor[1]))
        self.assertFalse(D.traversable(lvl, wall[0], wall[1]))
        with self.assertRaises(K.KinemaError) as cm:
            K.frames(lvl, floor, "a" * 64, lvl, wall, "b" * 64, 0, 6)
        self.assertEqual(cm.exception.code, "KINEMA-REFUSE")


class OneWay(unittest.TestCase):
    def test_own_source_is_one_way(self):
        self.assertTrue(K.the_membrane_is_one_way())

    def test_the_guard_bites_the_function_local_escape_hatch(self):
        # the escape hatch the tree's top-level-only guards leave open — kinema closes it
        self.assertFalse(K._source_is_one_way(
            "import gamegen\ndef f(s, t):\n    import enact as _E\n    return _E.dispatch(s, t)\n"))

    def test_the_guard_bites_a_top_level_authority_import(self):
        self.assertFalse(K._source_is_one_way("import move\n"))
        self.assertFalse(K._source_is_one_way("import descend\n"))

    def test_the_guard_bites_a_mutator_reach(self):
        self.assertFalse(K._source_is_one_way("import gamegen\nx = gamegen.step\n"))
        self.assertFalse(K._source_is_one_way("y = z.apply(1)\n"))

    def test_no_core_module_imports_kinema(self):
        # the forbidden direction: CORE -> KINEMA. Scan every game-layer module's module-scope imports.
        for name in ("gamegen", "descent", "move", "entity", "rngstream", "descend", "loot",
                     "combat", "heirloom", "actionlog", "savegame", "enact", "rerun", "statecanon"):
            with open(os.path.join(_T, name + ".py"), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            top = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    top.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    top.add((node.module or "").split(".")[0])
            self.assertNotIn("kinema", top, f"{name} imports kinema (a reverse CORE->VIEW edge)")


class ObserverPresence(unittest.TestCase):
    """D25 §14 — the observer-presence differential: does the existence of the observer alter the certified
    simulation at all?"""
    def _fingerprint(self):
        return (SC.statecanon_digest(), RP.rerun_digest(), EN.enact_digest(),
                SV.savegame_digest(), G.digest_of(0xC0FFEE, 2))

    def test_exercising_kinema_leaves_the_canonical_transcript_byte_identical(self):
        before = self._fingerprint()
        # a run's replay verdict, captured before the observer runs
        rec, _toks, _f = RP._saved_run(0xABCDE, 3, 3, 2)
        verdict_before = RP.verdict(rec)
        # exercise the observer over a real transition (and a descend, and a loot)
        rm = _real_move(0xC0FFEE, 2)
        s0, s1, dn, dn1 = rm
        K.frames(s0[0], s0[1], dn, s1[0], s1[1], dn1, 0, 144)
        # recapture: nothing canonical moved
        self.assertEqual(self._fingerprint(), before)
        self.assertEqual(RP.verdict(rec), verdict_before)


class Sampling(unittest.TestCase):
    def test_sample_count_is_view_only(self):
        for s, d in K.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(K.sampling_is_view_only(s, d))

    def test_witness_carried_verbatim(self):
        for s, d in K.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(K.the_witness_is_carried_verbatim(s, d))

    def test_a_bad_sample_count_refuses(self):
        for bad in (1, 0, -3, True, 2.0):
            with self.assertRaises(K.KinemaError):
                K.sample_alphas(bad)


class Arithmetic(unittest.TestCase):
    """D25 §10 Plant E — a one-ULP alpha perturbation is observable on the moving axis (the chosen law makes
    it so), and correctly invisible on a still axis."""
    def test_one_ulp_is_observable_on_the_moving_axis(self):
        # a unit move east: x moves (+1), y is still
        a, b = 5, 6
        mid = ONE // 2
        self.assertNotEqual(K._refine_axis(a, b, mid), K._refine_axis(a, b, mid + 1))   # moving: observable
        self.assertEqual(K._refine_axis(3, 3, mid), K._refine_axis(3, 3, mid + 1))      # still: invisible

    def test_endpoints_are_exact_in_q32_32(self):
        self.assertEqual(K._refine_axis(5, 6, 0), 5 * ONE)
        self.assertEqual(K._refine_axis(5, 6, ONE), 6 * ONE)


class Conformance(unittest.TestCase):
    def test_emitted_matches_pinned(self):
        self.assertTrue(K.emitted_matches_pinned())

    def test_scenes_and_top_reproduce(self):
        for n in K.SCENES:
            self.assertEqual(K.scene_result(n), K.golden(n))
        self.assertEqual(K.kinema_digest(), K.golden("kinema"))

    def test_an_unpinned_name_refuses_typed(self):
        self.assertTrue(K.an_unpinned_name_refuses())
        with self.assertRaises(K.KinemaError) as cm:
            K.golden("not-a-scene")
        self.assertEqual(cm.exception.code, "KINEMA-REFUSE")

    def test_layer_is_view(self):
        self.assertEqual(K.LAYER, "VIEW")
        self.assertEqual(K.ALLOWED_IMPORTS,
                         ("ast", "collections", "hashlib", "os", "gamegen", "descent", "field"))


if __name__ == "__main__":
    unittest.main()
