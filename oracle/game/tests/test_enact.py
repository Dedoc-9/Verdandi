# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `enact` (URDRENA1) — the typed action authority: a kind, a payload, and one
dispatch to the transition. The twelfth game-layer vertical slice, the prerequisite between `actionlog`
and `replay`.

The distinguishing claims, each a distinct failure surface:
  vocabulary   — the kinds are EXACTLY {MOVE, DESCEND, LOOT}; combat/heirloom are pure derivations, excluded.
  payload      — MOVE carries a direction; DESCEND/LOOT carry none; encode/decode round-trip.
  dispatch     — a routed kind EQUALS its authority (move.step/descend.descend/loot.loot) called directly.
  rng          — the stream advances only on LOOT (0 for MOVE and DESCEND) — presence != a draw.
  ordering     — actionlog's append order, not a second mechanism.
  ownership    — a bad TOKEN is ENACT-REFUSE; a bad STATE surfaces the AUTHORITY's code.
  neutral rule — actionlog -> decode -> dispatch reproduces the state savegame stored independently.

Dispatch faithfulness is checked against each authority directly and against the INDEPENDENT savegame store,
never against enact's own restatement."""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = os.path.join(ROOT, "tools", "terrain")
if _T not in sys.path:
    sys.path.insert(0, _T)

import enact as EN                                                       # noqa: E402
import move as M                                                        # noqa: E402
import descend as DE                                                    # noqa: E402
import loot as L                                                        # noqa: E402
import actionlog as A                                                   # noqa: E402
import gamegen as G                                                     # noqa: E402
import descent as D                                                     # noqa: E402
import rngstream as R                                                   # noqa: E402
import entity as E                                                      # noqa: E402
import savegame as SG                                                   # noqa: E402


def _origin(seed, depth, on="up"):
    lvl = G.generate(seed, depth)
    up, down = D.endpoints(lvl)
    return (lvl, up if on == "up" else down, R.root(seed))


class Vocabulary(unittest.TestCase):
    def test_kinds_are_exactly_the_three_transitions(self):
        self.assertEqual(EN.KINDS, ("MOVE", "DESCEND", "LOOT"))
        self.assertTrue(EN.the_kinds_are_exactly_the_state_transitions())

    def test_combat_and_heirloom_are_excluded_pure_derivations(self):
        self.assertTrue(EN.the_excluded_modules_are_pure_derivations())

    def test_combat_heirloom_really_import_no_state_module(self):
        # the exclusion is not a bare assertion: their AST carries no canonical-component import
        for mod in ("combat", "heirloom"):
            with open(os.path.join(_T, mod + ".py"), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            top = set()
            for node in tree.body:
                if isinstance(node, ast.Import):
                    top.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    top.add((node.module or "").split(".")[0])
            self.assertFalse({"gamegen", "entity", "rngstream", "move", "descend", "loot"} & top)


class Payload(unittest.TestCase):
    def test_token_round_trips_all_kinds_and_directions(self):
        self.assertTrue(EN.a_token_round_trips())
        for c in sorted(M.DIRECTIONS):
            self.assertEqual(EN.decode(EN.encode("MOVE", c)), ("MOVE", c))
        self.assertEqual(EN.decode(EN.encode("DESCEND")), ("DESCEND", None))
        self.assertEqual(EN.decode(EN.encode("LOOT")), ("LOOT", None))

    def test_move_requires_a_direction_payload(self):
        with self.assertRaises(EN.EnactError):
            EN.encode("MOVE")                                 # no direction
        with self.assertRaises(EN.EnactError):
            EN.encode("MOVE", "X")                            # not a direction

    def test_nullary_kinds_refuse_a_payload(self):
        for k in ("DESCEND", "LOOT"):
            with self.assertRaises(EN.EnactError):
                EN.encode(k, "N")

    def test_tokens_are_actionlog_tokens(self):
        # a produced token passes through actionlog unchanged (it is already canonical bytes)
        toks = (EN.encode("MOVE", "N"), EN.encode("LOOT"), EN.encode("DESCEND"))
        self.assertEqual(A.entries(A.from_actions(toks)), toks)


class DispatchMatchesAuthority(unittest.TestCase):
    def test_move_dispatch_matches_move_step(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(EN.move_dispatch_matches_the_authority(s, d))

    def test_descend_dispatch_matches_descend(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(EN.descend_dispatch_matches_the_authority(s, d))

    def test_loot_dispatch_matches_loot(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(EN.loot_dispatch_matches_the_authority(s, d))

    def test_dispatch_of_a_wrong_binding_would_diverge(self):
        # a LOOT dispatched where a MOVE was expected changes the stream, not the position — the bindings
        # are not interchangeable (guards against a router that ignored the kind)
        lvl, up, st = _origin(0, 1, "up")
        (l_m, p_m, s_m), _i = EN.dispatch((lvl, up, st), EN.encode("MOVE", "E"))
        (l_l, p_l, s_l), _j = EN.dispatch((lvl, up, st), EN.encode("LOOT"))
        self.assertEqual(s_m, st)              # move did not advance
        self.assertNotEqual(s_l, st)           # loot did
        self.assertEqual(p_l, up)              # loot did not move the entity


class RngPerKind(unittest.TestCase):
    def test_only_loot_advances_the_stream(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(EN.only_loot_advances_the_stream(s, d))

    def test_rng_advances_table(self):
        self.assertEqual((EN.rng_advances("MOVE"), EN.rng_advances("DESCEND"),
                          EN.rng_advances("LOOT")), (0, 0, 1))

    def test_a_move_dispatch_leaves_the_stream_a_fixed_point(self):
        lvl, up, st = _origin(0xDEADBEEF, 2, "up")
        (_l, _p, s2), _i = EN.dispatch((lvl, up, st), EN.encode("MOVE", "N"))
        self.assertEqual((s2.n, s2.r), (st.n, st.r))


class Ordering(unittest.TestCase):
    def test_ordering_is_actionlog_append(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(EN.the_ordering_is_actionlog_append(s, d))

    def test_reordering_loot_and_a_real_move_changes_the_stream(self):
        # loot's source is the entity POSITION, so reordering a LOOT relative to a move that actually
        # MOVES changes which source the loot folded -> the committed streams differ. Order is load-bearing.
        for s, d in G.CORPUS:
            lvl, up, _st = _origin(s, d, "up")
            for c in sorted(M.DIRECTIONS):
                if M.step(lvl, up, c)[0] == M.MOVED:
                    st = _origin(s, d, "up")
                    a, _i = EN.apply(st, (EN.encode("LOOT"), EN.encode("MOVE", c)))
                    b, _j = EN.apply(st, (EN.encode("MOVE", c), EN.encode("LOOT")))
                    self.assertEqual(a[1], b[1])             # position ends the same (loot never moves)
                    self.assertNotEqual(a[2], b[2])          # but the stream differs: loot folded a diff source
                    return
        self.skipTest("no moving direction on the corpus")   # not reached on this corpus


class Ownership(unittest.TestCase):
    def test_a_bad_token_is_ours_a_bad_state_is_the_authoritys(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(EN.a_bad_token_is_ours_a_bad_state_is_the_authoritys(s, d))

    def test_malformed_tokens_refuse_enact(self):
        for bad in (None, 0, "MN", b"", b"Q", b"MZ", b"DX", b"L!"):
            with self.assertRaises(EN.EnactError):
                EN.decode(bad)

    def test_a_valid_move_on_a_wall_surfaces_move_refuse(self):
        lvl = G.generate(0, 1)
        wall = None
        for y in range(lvl.h):
            for x in range(lvl.w):
                if lvl.cells[y][x:x + 1] == G.WALL:
                    wall = (x, y); break
            if wall:
                break
        with self.assertRaises(M.MoveError):
            EN.dispatch((lvl, wall, R.root(0)), EN.encode("MOVE", "N"))

    def test_refuse_is_total(self):
        self.assertEqual(EN.refuse_is_total(), (True, True))


class Router(unittest.TestCase):
    def test_router_reimplements_nothing(self):
        self.assertTrue(EN.the_router_reimplements_nothing())

    def test_declared_substrate_is_the_dispatch_stack(self):
        self.assertEqual(set(EN.ALLOWED_IMPORTS),
                         {"hashlib", "os", "gamegen", "move", "descend", "loot", "actionlog"})
        self.assertEqual(EN.LAYER, "CORE")


class NeutralRuler(unittest.TestCase):
    def test_dispatch_reproduces_the_savegame_ruler(self):
        for s, d in G.CORPUS:
            with self.subTest(seed=s, depth=d):
                self.assertTrue(EN.the_dispatch_reproduces_the_savegame_ruler(s, d))

    def test_the_ruler_is_independent_a_corruption_diverges(self):
        # build a run, store via savegame, corrupt one token, and require the reproduction to diverge
        toks = (EN.encode("LOOT"), EN.encode("MOVE", "E"), EN.encode("MOVE", "S"))
        st0 = _origin(7, 2, "up")
        (lvl_f, pos_f, stream_f), _i = EN.apply(st0, toks)
        rec = SG.serialize(7, 2, pos_f, stream_f, A.from_actions(toks))
        _s, _d, _lvl, _e, _st, log = SG.restore(rec)
        bad = list(A.entries(log))
        bad[1] = EN.encode("MOVE", "W")                      # E -> W
        (l_c, p_c, s_c), _j = EN.apply(_origin(7, 2, "up"), bad)
        self.assertNotEqual(p_c, pos_f)


class Conformance(unittest.TestCase):
    def test_emitted_matches_pinned(self):
        self.assertTrue(EN.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(EN.an_unpinned_name_refuses())

    def test_scenes_reproduce(self):
        for n in EN.SCENES:
            self.assertEqual(EN.scene_result(n), EN.golden(n))
        self.assertEqual(EN.enact_digest(), EN.golden("enact"))


if __name__ == "__main__":
    unittest.main()
