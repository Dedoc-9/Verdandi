# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `rerun` (URDRRRN1) — the recovered action history must reproduce the
independently stored state. The thirteenth game-layer vertical slice, a certification layer over
`actionlog`/`savegame`/`enact`, adding no simulation authority.

The distinguishing claims, each a distinct failure surface:
  origin       — reconstructed from earned state (seed, depth − DESCEND count, spawn, root); Slice B closed.
  reproduce    — the from-origin fold matches the independently stored savegame, bit-for-bit.
  bind         — an envelope-valid record whose log ≠ its stored state DIVERGES (the check savegame declines).
  discriminate — the ruler is (pos, stream); depth equality is tautological, never the ruler.
  ownership    — underflow is RERUN-REFUSE; bad token/record/descend surface their own authority's code.
  no authority — the fold IS enact.apply; replay advances no RNG and mints no transition (AST)."""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = os.path.join(ROOT, "tools", "terrain")
if _T not in sys.path:
    sys.path.insert(0, _T)

import rerun as RP                                                      # noqa: E402
import savegame as SV                                                   # noqa: E402
import actionlog as A                                                   # noqa: E402
import enact as EN                                                      # noqa: E402
import gamegen as G                                                     # noqa: E402
import rngstream as R                                                   # noqa: E402
import move as M                                                        # noqa: E402
import descend as DE                                                    # noqa: E402


class OriginReconstruction(unittest.TestCase):
    def test_origin_recovers_across_the_corpus(self):
        for s, d, f, l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.a_run_reproduces_and_recovers_its_origin(s, d, f, l))

    def test_depth0_is_current_minus_descend_count(self):
        rec, toks, _ = RP._saved_run(0xC0FFEE, 2, 3, 2)
        seed, depth, _l, _e, _s, log = SV.restore(rec)
        self.assertEqual(depth - RP.descend_count(log), 2)   # origin depth, not the current depth (4)
        self.assertNotEqual(depth, 2)                        # current depth really did move

    def test_origin_is_spawn_and_root(self):
        lvl0, pos0, stream0 = RP.reconstruct_origin(7, 5, A.empty())
        self.assertEqual(pos0, M.spawn(G.generate(7, 5)))
        self.assertEqual(stream0, R.root(7))
        self.assertEqual(lvl0.depth, 5)


class Reproduce(unittest.TestCase):
    def test_multi_floor_reproduces(self):
        for s, d, f, l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                rec, _t, _f = RP._saved_run(s, d, f, l)
                self.assertEqual(RP.verdict(rec), RP.REPRODUCED)

    def test_deep_single_floor_reproduces(self):
        self.assertTrue(RP.a_deep_single_floor_run_reproduces(7, 5))
        self.assertTrue(RP.a_deep_single_floor_run_reproduces(1, 4))

    def test_empty_log_replays_to_origin(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.the_empty_log_replays_to_the_origin(s, d))

    def test_reproduce_matches_savegame_component_digests(self):
        rec, _t, _f = RP._saved_run(0, 1, 3, 2)
        _s, _d, level, ent, stream, _log = SV.restore(rec)
        v, (lvl, pos, strm) = RP.replay(rec)
        self.assertEqual(v, RP.REPRODUCED)
        self.assertEqual(G.level_digest(lvl), G.level_digest(level))
        self.assertEqual(pos, ent.get("pos"))
        self.assertEqual(strm, stream)


class TheBinding(unittest.TestCase):
    def test_corrupted_history_diverges(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.a_corrupted_history_diverges(s, d))

    def test_reordered_history_diverges(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.a_reordered_history_diverges(s, d))

    def test_deleted_action_diverges(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.a_deleted_action_diverges(s, d))

    def test_inconsistent_pair_diverges(self):
        # the check savegame declines to make: it stored the log and the state independently
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.an_inconsistent_pair_diverges(s, d))

    def test_savegame_itself_would_accept_the_inconsistent_pair(self):
        # proves the binding is replay's, not savegame's: savegame.restore is happy with a log that does
        # not fold to the stored state (it stores them independently)
        rec, toks, _f = RP._saved_flat_run(0, 1, 4, 3)
        incon = RP._tamper_log(rec, list(toks)[:-1])
        SV.restore(incon)                                    # no raise — savegame accepts it
        self.assertEqual(RP.verdict(incon), RP.DIVERGED)     # replay catches it


class Discriminator(unittest.TestCase):
    def test_ruler_is_pos_and_stream_not_depth(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                depth_taut, diverged, discriminated = RP.the_discriminator_is_pos_and_stream(s, d)
                self.assertTrue(depth_taut)       # folded depth == stored depth (tautological)
                self.assertTrue(diverged)         # yet the verdict is DIVERGED
                self.assertTrue(discriminated)    # carried by pos or stream

    def test_only_loot_advances_across_a_replay(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.only_loot_advances_across_a_replay(s, d))


class Ownership(unittest.TestCase):
    def test_origin_underflow_is_replay_refuse(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.origin_underflow_refuses(s, d))

    def test_underflow_raises_typed(self):
        rec, _t, _f = RP._saved_run(0, 1, 1, 1)
        seed, depth, _l, ent, stream, _log = SV.restore(rec)
        many = A.from_actions(tuple(EN.encode(EN.DESCEND) for _ in range(depth + 1)))
        bad = SV.serialize(seed, depth, ent.get("pos"), stream, many)
        with self.assertRaises(RP.RerunError):
            RP.replay(bad)

    def test_bogus_descend_surfaces_descend_refuse(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.a_bogus_descend_surfaces_the_authority(s, d))

    def test_malformed_record_is_savegame_refuse(self):
        self.assertTrue(RP.a_malformed_record_is_savegames_refusal())
        with self.assertRaises(SV.SavegameError):
            RP.replay(b"not a record")

    def test_malformed_token_is_enact_refuse(self):
        for s, d, _f, _l in RP.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(RP.a_malformed_token_is_enacts_refusal(s, d))

    def test_refuse_is_total(self):
        self.assertEqual(RP.refuse_is_total(0, 1), (True, True, True))


class NoAuthority(unittest.TestCase):
    def test_fold_adds_no_authority(self):
        self.assertTrue(RP.the_fold_adds_no_authority())

    def test_declared_substrate_and_no_lockstep(self):
        self.assertEqual(set(RP.ALLOWED_IMPORTS),
                         {"hashlib", "os", "gamegen", "move", "rngstream", "entity", "actionlog",
                          "enact", "savegame"})
        with open(os.path.join(_T, "rerun.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        top = set()
        for node in tree.body:
            if isinstance(node, ast.Import):
                top.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                top.add((node.module or "").split(".")[0])
        self.assertNotIn("lockstep", top)
        self.assertEqual(RP.LAYER, "CORE")

    def test_fold_equals_enact_apply(self):
        # the fold IS enact.apply — replay owns orchestration, not transition math
        rec, _t, _f = RP._saved_run(0, 1, 2, 2)
        seed, depth, _l, _e, _s, log = SV.restore(rec)
        origin = RP.reconstruct_origin(seed, depth, log)
        (lvl, pos, strm), _ = EN.apply(origin, A.entries(log))
        v, (lvl2, pos2, strm2) = RP.replay(rec)
        self.assertEqual((G.level_digest(lvl), pos, strm), (G.level_digest(lvl2), pos2, strm2))


class Conformance(unittest.TestCase):
    def test_emitted_matches_pinned(self):
        self.assertTrue(RP.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(RP.an_unpinned_name_refuses())

    def test_scenes_reproduce(self):
        for n in RP.SCENES:
            self.assertEqual(RP.scene_result(n), RP.golden(n))
        self.assertEqual(RP.rerun_digest(), RP.golden("rerun"))


if __name__ == "__main__":
    unittest.main()
