# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `gamegen` (URDRGEN1) — seed + depth -> canonical level -> digest.

  THE CONTRACT IS HELD, CLAUSE BY CLAUSE: the domain refuses at both ends, the corpus reproduces raw,
    identity is a function of the input alone (three fresh interpreters under different hash seeds
    print one digest), and the deepest admissible level GENERATES rather than merely being storable.
  THE DIGEST IS NOT THE ORACLE: structure has its own predicates, and each is proved live by a
    planted violation caught BY NAME.
  THE INERT PLANT IS REPORTED AS INERT; the observable ones move.
  D24 §6 IS CHECKED FROM OUTSIDE: the module's imports are read from its AST here, because a module
    that graded its own imports would need `ast`.

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

import gamegen as G                                                       # noqa: E402

SRC_PATH = os.path.join(_T, "gamegen.py")
LV = G.generate(*G.CORPUS[0])


class TheDomain(unittest.TestCase):
    def test_every_listed_bad_input_refuses_typed(self):
        for s, d in G.REFUSED_INPUTS:
            with self.subTest(seed=s, depth=d):
                with self.assertRaises(G.GamegenError) as cm:
                    G.check_params(s, d)
                self.assertEqual(cm.exception.code, "GAMEGEN-REFUSE")

    def test_the_four_corners_are_admitted(self):
        for s, d in G.ADMITTED_CORNERS:
            with self.subTest(seed=s, depth=d):
                G.check_params(s, d)
        self.assertEqual(G.refusal_is_total(), (True, True))

    def test_a_bool_is_not_an_int_here(self):
        with self.assertRaises(G.GamegenError):
            G.generate(True, 1)
        with self.assertRaises(G.GamegenError):
            G.generate(0, True)

    def test_refusal_is_a_refusal_and_not_a_clamp(self):
        """A clamped depth would generate SOME level; a refusal generates none."""
        with self.assertRaises(G.GamegenError):
            G.generate(0, G.DEPTH_MAX + 1)
        with self.assertRaises(G.GamegenError):
            G.generate(G.SEED_MAX + 1, 1)


class DepthIsThreeClaims(unittest.TestCase):
    def test_representation_the_bound_is_derived_and_equals_its_literal(self):
        self.assertEqual(G.DEPTH_MAX, 2147483647)
        self.assertEqual(G.DEPTH_MAX, (1 << (32 - 1)) - 1)
        self.assertEqual(G.DEPTH_BITS, 31)
        self.assertTrue(G.depth_max_is_derived_not_restated())

    def test_admission_the_domain_is_closed_at_both_ends(self):
        G.check_params(0, 1)
        G.check_params(0, G.DEPTH_MAX)
        with self.assertRaises(G.GamegenError):
            G.check_params(0, 0)
        with self.assertRaises(G.GamegenError):
            G.check_params(0, G.DEPTH_MAX + 1)

    def test_generation_the_deepest_level_actually_generates(self):
        """A generator that merely stores a legal integer gets no credit."""
        deep = G.the_deepest_level_generates()
        self.assertEqual(len(deep), 2)
        for s, ok, rooms in deep:
            with self.subTest(seed=s):
                self.assertTrue(ok)
                self.assertGreaterEqual(rooms, G.ROOMS_MIN)
        lv = G.generate(7, G.DEPTH_MAX)
        self.assertEqual(lv.depth, G.DEPTH_MAX)
        self.assertEqual(G.level_digest(lv), G.golden(G.corpus_name(7, G.DEPTH_MAX)))

    def test_depth_reaches_only_the_preimage(self):
        """The same seed at two depths draws the same NUMBER of times and differs in bytes."""
        a, b = G.generate(3, 1), G.generate(3, G.DEPTH_MAX)
        self.assertEqual(len(a.rooms), len(b.rooms))
        self.assertNotEqual(G.canon_bytes(a), G.canon_bytes(b))


class TheCanon(unittest.TestCase):
    def test_the_corpus_reproduces_raw(self):
        for n, d in G.corpus_digests():
            with self.subTest(level=n):
                self.assertEqual(d, G.golden(n))

    def test_scene_goldens_and_the_top_digest(self):
        for n in G.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(G.scene_result(n), G.golden(n))
        self.assertEqual(G.gamegen_digest(), G.golden("gamegen"))
        self.assertTrue(G.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(G.an_unpinned_name_refuses())
        with self.assertRaises(G.GamegenError):
            G.golden("level-99-99")

    def test_the_eight_are_pairwise_distinct_and_neighbours_differ(self):
        self.assertTrue(G.the_corpus_is_distinct())
        self.assertTrue(G.neighbours_differ())

    def test_identity_is_the_declared_bytes_and_nothing_else(self):
        cb = G.canon_bytes(LV)
        self.assertTrue(cb.startswith(b"URDRGEN1|s:0|d:1|48x32|rooms:"))
        self.assertEqual(cb.count(b"|"), 5 + G.H - 1)
        self.assertEqual(len(cb.split(b"|")[-1]), G.W)

    def test_determinism_ten_times_is_a_property_of_the_run_and_the_pin_is_the_claim(self):
        d = [G.digest_of(1, 1) for _ in range(10)]
        self.assertEqual(len(set(d)), 1)
        self.assertEqual(d[0], G.golden(G.corpus_name(1, 1)))


class IdentityIsAFunctionOfTheInputAlone(unittest.TestCase):
    def test_three_fresh_interpreters_under_different_hash_seeds_print_one_digest(self):
        """THE INVARIANCE LAW, MEASURED WHERE IT CAN BE: a hash seed cannot be varied inside a
        process, so three fresh ones are asked."""
        code = ("import sys; sys.path.insert(0, %r); import gamegen as G; "
                "print(G.digest_of(12345, 1))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            p = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=120)
            self.assertEqual(p.returncode, 0, p.stderr)
            outs.append(p.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)
        self.assertEqual(outs[0], G.golden(G.corpus_name(12345, 1)))

    def test_the_room_order_is_inert_and_is_reported_as_such(self):
        self.assertTrue(G.the_room_order_is_inert(LV))

    def test_a_moved_cell_is_observable(self):
        self.assertTrue(G.a_moved_cell_is_observable(LV))

    def test_the_mutated_generator_diverges_on_every_corpus_member(self):
        """`heightfield`'s corpus law: a plausible generator with the opposite bend moves every pin."""
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(G.the_mutated_generator_diverges(s, d))

    def test_the_draw_is_stateless(self):
        """The same draw asked twice, and asked after other draws, is the same draw."""
        a = G._draw(5, 9, "room-x", 3)
        G._draw(5, 9, "room-x", 4)
        G._draw(6, 9, "room-x", 3)
        self.assertEqual(a, G._draw(5, 9, "room-x", 3))
        self.assertNotEqual(a, G._draw(5, 9, "room-y", 3))


class StructureNotDigest(unittest.TestCase):
    def test_the_corpus_is_well_formed(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertEqual(G.problems(G.generate(s, d)), [])

    def test_the_sweep_is_clean_and_the_refusal_count_is_reported(self):
        gen, ref, mal, lo, hi = G.sweep()
        self.assertEqual((gen, mal), (128, 0))
        self.assertGreaterEqual(lo, G.ROOMS_MIN)
        self.assertLessEqual(hi, G.ROOMS_MAX)
        self.assertEqual(ref, 0, "the admission condition was met live — a finding, record it")

    def test_every_plant_is_caught_by_its_own_name(self):
        for kind, caught in G.every_plant_is_caught_by_name(LV):
            with self.subTest(plant=kind):
                self.assertTrue(caught, f"{kind} was not caught by the predicate it targets")

    def test_the_plants_leave_the_original_alone(self):
        before = G.level_digest(LV)
        G.plants(LV)
        G.every_plant_is_caught_by_name(LV)
        self.assertEqual(G.level_digest(LV), before)
        self.assertEqual(G.problems(LV), [])

    def test_the_admission_condition_is_real(self):
        self.assertTrue(G.the_admission_condition_is_real())

    def test_the_border_is_wall_and_the_stairs_are_two_and_in_rooms(self):
        self.assertTrue(all(c == G.WALL[0] for c in LV.cells[0]))
        self.assertTrue(all(c == G.WALL[0] for c in LV.cells[-1]))
        self.assertTrue(all(r[0:1] == G.WALL and r[-1:] == G.WALL for r in LV.cells))
        flat = b"".join(LV.cells)
        self.assertEqual((flat.count(G.UP), flat.count(G.DOWN)), (1, 1))

    def test_the_rooms_are_sorted_and_within_bounds(self):
        self.assertEqual(LV.rooms, tuple(sorted(LV.rooms)))
        for (x, y, w, h) in LV.rooms:
            self.assertTrue(1 <= x and x + w <= G.W - 1 and 1 <= y and y + h <= G.H - 1)

    def test_render_is_a_view_and_not_identity(self):
        txt = G.render(LV)
        self.assertEqual(len(txt.splitlines()), G.H)
        self.assertNotIn(b"URDRGEN1", txt.encode())


class AdmittedUnderD24(unittest.TestCase):
    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(G.LAYER, "CORE")
        self.assertEqual(G.D24_ANSWER, "affects canonical game state")

    def test_the_imports_are_exactly_the_declared_substrate(self):
        """D24 §6 rule 1, read off the AST: the core imports nothing the gate does not already run
        on — and nothing under `tools/` at all."""
        with io.open(SRC_PATH, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        found = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        self.assertEqual(found, set(G.ALLOWED_IMPORTS), found)
        for name in found:
            self.assertIn(name, sys.stdlib_module_names, f"{name} is not the standard library")

    def test_no_view_vocabulary_reaches_the_module(self):
        """A generator that names a renderer, a window or a clock has crossed §1."""
        with io.open(SRC_PATH, encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        for forbidden in ("time", "random", "threading", "socket", "tkinter", "pygame"):
            self.assertNotIn(forbidden, names)


if __name__ == "__main__":
    unittest.main()
