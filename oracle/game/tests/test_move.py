# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `move` (URDRMOV1) — the first authoritative D_n -> D_{n+1}.

  THE STEP AGREES WITH `descent`'s AUTHORITY, never a copy of it: MOVED iff the target is
    `descent.traversable`, BLOCKED (D_{n+1} = D_n) otherwise — and a `descent.seal_down`
    counterexample flips a step that MOVED into one that is BLOCKED.
  BLOCKED IS A LEGAL OUTCOME, not an error: a wall step returns D_{n+1} = D_n, the pair KINEMA's
    Plant A consumes; REFUSE is reserved for MALFORMED input.
  IDENTITY IS DERIVED, not parallel: the state names the level by `gamegen.level_digest` and adds the
    position field; a MOVED step changes the digest, a BLOCKED step does not.
  THE DEPENDENCY RUNS ONE WAY and the movement model IS `descent`'s adjacency.

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

import move as M                                                          # noqa: E402
import descent as D                                                       # noqa: E402
import gamegen as G                                                       # noqa: E402

LV = G.generate(*M.CORPUS[0])
P = M.spawn(LV)


class TheStepAgreesWithDescent(unittest.TestCase):
    def test_move_iff_descent_says_the_target_is_traversable(self):
        for s, d in M.CORPUS:
            lv = G.generate(s, d)
            p = M.spawn(lv)
            for c in M.DIRECTIONS:
                with self.subTest(seed=s, depth=d, cmd=c):
                    self.assertTrue(M.a_step_agrees_with_descent(lv, p, c))

    def test_legality_comes_from_descent_not_a_local_copy(self):
        """The whole point of exposing `descent.traversable`: a move is legal because DESCENT says
        the cell is, and `move` re-checks nothing of its own."""
        dx, dy = M.DIRECTIONS["E"]
        target = (P[0] + dx, P[1] + dy)
        outcome, _nxt = M.step(LV, P, "E")
        self.assertEqual(outcome == M.MOVED, D.traversable(LV, *target))

    def test_the_directions_are_descents_adjacency(self):
        self.assertTrue(M.the_directions_are_descents())
        self.assertEqual(sorted(M.DIRECTIONS.values()), sorted(D.STEPS))

    def test_a_sealed_mouth_flips_moved_into_blocked(self):
        """LEGALITY TRACKS `descent`'s AUTHORITY, on a counterexample: sealing the stairs-down room
        changes `descent.traversable`, and the SAME step that MOVED is now BLOCKED wherever the seal
        walled its target."""
        for s, d in M.CORPUS:
            with self.subTest(seed=s, depth=d):
                found, tracked = M.a_sealed_mouth_blocks_a_step_that_moved(s, d)
                self.assertTrue(found, "no MOVED step from the spawn to seal against")
                self.assertTrue(tracked, "sealing did not flip MOVED->BLOCKED on the walled target")


class BlockedIsALegalOutcome(unittest.TestCase):
    def test_a_wall_step_is_blocked_not_refused(self):
        cur = P
        blocked = None
        for _ in range(LV.w + LV.h):
            outcome, cur = M.step(LV, cur, "W")
            if outcome == M.BLOCKED:
                blocked = cur
                break
        self.assertIsNotNone(blocked, "a westward walk never hit a wall on a bounded level")

    def test_blocked_is_a_fixed_point_in_state_and_digest(self):
        for s, d in M.CORPUS:
            lv = G.generate(s, d)
            p = M.spawn(lv)
            for c in M.DIRECTIONS:
                with self.subTest(seed=s, cmd=c):
                    self.assertTrue(M.a_blocked_step_is_a_fixed_point(lv, p, c))

    def test_a_walk_into_the_wall_blocks_well_formed_on_every_level(self):
        for s, d in M.CORPUS:
            with self.subTest(seed=s, depth=d):
                saw, well = M.a_walk_reaches_a_wall_and_blocks(G.generate(s, d))
                self.assertTrue(saw)
                self.assertTrue(well)

    def test_off_grid_is_blocked_not_refused(self):
        for x in range(1, LV.w - 1):
            if D.traversable(LV, x, 1):
                o, n = M.step(LV, (x, 1), "N")
                self.assertEqual(o, M.BLOCKED)
                self.assertEqual(n, (x, 1))
                break


class MovedChangesCanonicalState(unittest.TestCase):
    def test_a_moved_step_moves_position_and_digest(self):
        for s, d in M.CORPUS:
            lv = G.generate(s, d)
            p = M.spawn(lv)
            for c in M.DIRECTIONS:
                with self.subTest(seed=s, cmd=c):
                    self.assertTrue(M.a_moved_step_changes_the_state(lv, p, c))

    def test_identity_names_the_level_and_the_entity_by_their_digests(self):
        """One content-addressed vocabulary: the state bytes carry `gamegen.level_digest` AND the
        entity's `entity.entity_digest`, not a re-serialized level or an inline `pos:x,y`. The entity
        component carries the position, and `move` references it the same way it references the level."""
        import entity as E
        sb = M.state_bytes(LV, P)
        self.assertIn(G.level_digest(LV).encode(), sb)
        self.assertTrue(sb.startswith(b"URDRMOV1|lvl:"))
        self.assertIn(b"|ent:" + E.digest_at(P).encode(), sb)
        self.assertNotIn(b"|pos:", sb)

    def test_two_positions_on_one_level_have_distinct_state_digests(self):
        o, nxt = M.step(LV, P, "E")
        self.assertEqual(o, M.MOVED)
        self.assertNotEqual(M.state_digest(LV, P), M.state_digest(LV, nxt))


class TheRefuseDomain(unittest.TestCase):
    def test_a_malformed_command_refuses_typed(self):
        for bad in ("north", "", "NN", 0, None, ("N",)):
            with self.subTest(cmd=bad):
                with self.assertRaises(M.MoveError) as cm:
                    M.step(LV, P, bad)
                self.assertEqual(cm.exception.code, "MOVE-REFUSE")

    def test_a_malformed_state_refuses_typed(self):
        for bad in M._bad_states(LV):
            with self.subTest(pos=bad):
                with self.assertRaises(M.MoveError) as cm:
                    M.step(LV, bad, "N")
                self.assertEqual(cm.exception.code, "MOVE-REFUSE")

    def test_an_entity_on_a_wall_refuses_not_blocks(self):
        """A malformed D_n is a REFUSE, distinct from a wall STEP which is BLOCKED."""
        wall = M._bad_states(LV)[0]
        self.assertFalse(D.traversable(LV, *wall))
        with self.assertRaises(M.MoveError):
            M.step(LV, wall, "N")

    def test_refuse_is_total(self):
        self.assertEqual(M.refuse_is_total(LV), (True, True))

    def test_the_spawn_is_descents_endpoint(self):
        self.assertTrue(M.the_spawn_is_descents_endpoint(LV))
        self.assertEqual(M.spawn(LV), D.endpoints(LV)[0])


class DeterminismAndLayer(unittest.TestCase):
    def test_step_is_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import move as M, gamegen as G; "
                "lv = G.generate(12345, 1); p = M.spawn(lv); "
                "print('|'.join('%%s,%%s' %% M.step(lv, p, c) for c in sorted(M.DIRECTIONS)))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)

    def test_apply_folds_a_sequence_deterministically(self):
        final, outcomes = M.apply(LV, P, ["E", "E", "W", "W"])
        self.assertEqual(len(outcomes), 4)
        self.assertEqual(M.apply(LV, P, ["E", "E", "W", "W"]), (final, outcomes))

    def test_imports_are_the_declared_substrate_and_one_way(self):
        found = self._imports("move.py")
        self.assertEqual(found, set(M.ALLOWED_IMPORTS))
        for name in ("gamegen", "descent"):
            self.assertIn(name, found)
        self.assertNotIn("move", self._imports("descent.py"))
        self.assertNotIn("move", self._imports("gamegen.py"))

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(M.LAYER, "CORE")
        self.assertIn("canonical game state", M.D24_ANSWER)

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
        for n in M.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(M.scene_result(n), M.golden(n))
        self.assertEqual(M.move_digest(), M.golden("move-digest"))
        self.assertTrue(M.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(M.an_unpinned_name_refuses())
        with self.assertRaises(M.MoveError):
            M.golden("wishful")


if __name__ == "__main__":
    unittest.main()
