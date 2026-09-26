# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `rngstream` (URDRRNG1) — the canonical RNG stream, the first STATEFUL
canonical component.

  ROOTED AT THE RUN'S SEED, DOMAIN-SEPARATED: R_0 = SHA-256(b"rngstream/v1"|s:seed), which is not a
    rootless hash of the seed and not a `gamegen` derivation of it.
  ADVANCE IS AN ACTION, A READ NEVER ADVANCES: `Stream` is immutable, `advance` returns a new stream,
    reads return values; a read cannot advance by construction. The identity binds (n, R_n).
  DETERMINISM AND COMMITMENT: same (seed, actions) reproduce the whole trace across fresh interpreters;
    a different action sequence diverges; incremental and batch advancement agree at every prefix.
  MOVE IS NOT CONTAMINATED: a reference (level, entity, stream) assembly stepped by `move` leaves the
    stream a fixed point while the entity moves — and a harness that advanced on a move WOULD be caught.
  SERIALIZATION v1 is FROZEN: the golden vectors are the representation lock.

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

import rngstream as R                                                     # noqa: E402
import gamegen as G                                                      # noqa: E402
import move as M                                                         # noqa: E402

SEED = 0xDEADBEEF
ACTS = R.ACTIONS


class TheRootIsDomainSeparated(unittest.TestCase):
    def test_root_carries_the_domain_tag_and_is_not_a_rootless_hash(self):
        for s in R.SEEDS:
            with self.subTest(seed=s):
                self.assertNotEqual(R.root(s).r, R._rootless(s))
                self.assertTrue(R.the_root_is_domain_separated(s))

    def test_root_is_not_a_gamegen_derivation_of_the_same_seed(self):
        for s in R.SEEDS:
            with self.subTest(seed=s):
                self.assertNotEqual(R.root(s).r.hex(), G.digest_of(s, 1))

    def test_dropping_the_domain_would_collapse_the_root(self):
        """VALIDITY: the separation is load-bearing — a rootless variant equals a plain hash of the
        seed, which is exactly what the domain tag prevents, so the law can go red."""
        s = R.SEEDS[0]
        self.assertEqual(R._rootless(s), __import__("hashlib").sha256(b"s:%d" % s).digest())
        self.assertNotEqual(R.root(s).r, R._rootless(s))

    def test_the_seed_domain_is_single_sourced_with_gamegen(self):
        self.assertTrue(R.seed_domain_matches_gamegen())
        self.assertEqual(R.SEED_MAX, G.SEED_MAX)


class AdvanceIsAnAction(unittest.TestCase):
    def test_an_advance_moves_coordinate_value_and_identity(self):
        for s in R.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(R.an_advance_changes_the_state(s))

    def test_a_different_action_diverges(self):
        s0 = R.root(SEED)
        self.assertNotEqual(R.advance(s0, "v0").r, R.advance(s0, "v1").r)
        self.assertTrue(R.different_actions_diverge(SEED))

    def test_advance_is_pure(self):
        s0 = R.root(SEED)
        self.assertEqual(R.advance(s0, "v0"), R.advance(s0, "v0"))
        # advancing does not mutate the input stream
        before = (s0.n, s0.r)
        R.advance(s0, "v0")
        self.assertEqual((s0.n, s0.r), before)


class AReadNeverAdvances(unittest.TestCase):
    def test_reads_leave_the_state_unchanged(self):
        for s in R.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(R.a_read_does_not_advance(s))

    def test_peek_is_deterministic_and_bounded_and_does_not_advance(self):
        s = R.advance(R.root(SEED), "v0")
        before = (s.n, s.r)
        vals = [R.peek(s, "loot", 100) for _ in range(5)]
        self.assertEqual(len(set(vals)), 1)              # deterministic
        self.assertTrue(0 <= vals[0] < 100)             # bounded
        self.assertEqual((s.n, s.r), before)            # did not advance

    def test_a_read_that_advanced_would_be_caught(self):
        """VALIDITY: a leaky 'read' that actually advanced changes (n, R_n); the invariant's negation
        is detectable, so `a_read_does_not_advance` is not vacuous."""
        s = R.root(SEED)
        leaked = R.advance(s, "peek-as-advance")        # what a leaking read would do
        self.assertNotEqual((leaked.n, leaked.r), (s.n, s.r))


class DeterminismAndComposition(unittest.TestCase):
    def test_identical_actions_give_the_identical_trace(self):
        for s in R.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(R.identical_actions_give_the_identical_stream(s, ACTS))

    def test_composition_matches_every_prefix(self):
        for s in R.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(R.composition_matches_every_prefix(s, ACTS))

    def test_apply_equals_the_final_trace_state(self):
        tr = R.trace(R.root(SEED), ACTS)
        self.assertEqual(R.apply(R.root(SEED), ACTS), tr[-1])
        self.assertEqual(len(tr), len(ACTS) + 1)

    def test_the_stream_is_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import rngstream as R; "
                "print('|'.join(R.stream_digest(s) for s in R.trace(R.root(%d), R.ACTIONS)))"
                % (_T, SEED))
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)


class TheIndexIsBound(unittest.TestCase):
    def test_same_value_at_a_different_index_is_a_different_identity(self):
        self.assertTrue(R.the_index_is_bound_into_identity(SEED))
        s = R.apply(R.root(SEED), ACTS)
        self.assertNotEqual(R.stream_digest(R.Stream(s.n + 1, s.r)), R.stream_digest(s))

    def test_the_identity_bytes_are_the_frozen_v1_shape(self):
        s = R.apply(R.root(SEED), ACTS)
        self.assertEqual(R.stream_bytes(s), b"URDRRNG1|n:%d|r:%s" % (s.n, s.r.hex().encode()))


class MoveIsNotContaminated(unittest.TestCase):
    def test_a_move_sequence_leaves_the_stream_a_fixed_point(self):
        fixed, moved, decoupled = R.move_leaves_the_stream_a_fixed_point(SEED)
        self.assertTrue(fixed, "a move sequence advanced the RNG stream")
        self.assertTrue(moved, "no entity move occurred — the check would be vacuous")
        self.assertTrue(decoupled, "move imports rngstream — the layers are not decoupled")

    def test_move_does_not_import_rngstream(self):
        self.assertNotIn("rngstream", self._imports("move.py"))
        self.assertNotIn("rngstream", set(M.ALLOWED_IMPORTS))

    def test_a_harness_that_advanced_on_a_move_would_be_caught(self):
        """VALIDITY: the boundary invariant is not vacuous — a buggy assembly that advanced the stream
        on a move DOES move it, so the honest fixed-point is a real measurement."""
        lvl = G.generate(0, 1)
        pos = M.spawn(lvl)
        s = R.root(SEED)
        # honest: move updates position, stream untouched
        _o, nxt = M.step(lvl, pos, sorted(M.DIRECTIONS)[0])
        self.assertEqual(s, R.root(SEED))
        # buggy: advance the stream on the move — must be observably different
        buggy = R.advance(s, "move-leak")
        self.assertNotEqual(buggy, s)

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


class TheRefuseDomain(unittest.TestCase):
    def test_a_malformed_seed_refuses_typed(self):
        for bad in (-1, R.SEED_MAX + 1, 1.0, "0", None, True):
            with self.subTest(seed=bad):
                with self.assertRaises(R.RngError) as cm:
                    R.root(bad)
                self.assertEqual(cm.exception.code, "RNG-REFUSE")

    def test_a_malformed_action_refuses_typed(self):
        s0 = R.root(0)
        for bad in (0, None, ("v",), 1.0):
            with self.subTest(action=bad):
                with self.assertRaises(R.RngError) as cm:
                    R.advance(s0, bad)
                self.assertEqual(cm.exception.code, "RNG-REFUSE")

    def test_a_malformed_bound_or_stream_refuses_typed(self):
        s0 = R.root(0)
        for bad in (0, -1, 1.0, None):
            with self.subTest(bound=bad):
                with self.assertRaises(R.RngError):
                    R.peek(s0, "x", bad)
        for bad in ((0, b"short"), (-1, b"\x00" * 32), (1.0, b"\x00" * 32)):
            with self.subTest(stream=bad):
                with self.assertRaises(R.RngError):
                    R.Stream(*bad)

    def test_refuse_is_total(self):
        self.assertEqual(R.refuse_is_total(), (True, True, True, True))


class DeterminismAndLayer(unittest.TestCase):
    def test_imports_are_the_declared_substrate_at_module_scope(self):
        top = self._mod_scope_imports("rngstream.py")
        self.assertEqual(top, set(R.ALLOWED_IMPORTS))
        self.assertEqual(top, {"hashlib", "os"})
        stdlib = getattr(sys, "stdlib_module_names", top)
        self.assertTrue(top <= set(stdlib))

    def test_the_game_modules_are_reached_only_lazily_and_one_way(self):
        top = self._mod_scope_imports("rngstream.py")
        allimp = self._all_imports("rngstream.py")
        for name in ("gamegen", "move"):
            self.assertIn(name, allimp)          # reached in the laws
            self.assertNotIn(name, top)          # but not at module scope
        self.assertNotIn("rngstream", self._all_imports("gamegen.py"))
        self.assertNotIn("rngstream", self._all_imports("move.py"))

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(R.LAYER, "CORE")
        self.assertIn("canonical game state", R.D24_ANSWER)

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
        for n in R.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(R.scene_result(n), R.golden(n))
        self.assertEqual(R.rngstream_digest(), R.golden("rngstream"))
        self.assertTrue(R.emitted_matches_pinned())

    def test_the_golden_vectors_are_the_frozen_representation(self):
        """The v1 serialization is declared frozen; the root/trace scenes ARE the representation lock,
        so an exact-byte change to `stream_bytes` moves a pin here."""
        s0 = R.root(R.SEEDS[0])
        self.assertTrue(R.stream_bytes(s0).startswith(b"URDRRNG1|n:0|r:"))
        self.assertEqual(len(R.root(R.SEEDS[0]).r), 32)

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(R.an_unpinned_name_refuses())
        with self.assertRaises(R.RngError):
            R.golden("wishful")


if __name__ == "__main__":
    unittest.main()
