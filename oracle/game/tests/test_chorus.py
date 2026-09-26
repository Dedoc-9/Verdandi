# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `chorus` (URDRCHO1) — the composition of N disposable observers over one
authoritative transition. WINDOW-0 of the observer-composition arc; the second game-layer VIEW module.

Invariant under test: OBSERVER TOPOLOGY IS DISPOSABLE; CANONICAL SIMULATION IS NOT.

Distinct failure surfaces:
  compose       — compose is repeated kinema application; N=0/1/2 natural; no N-window authority.
  agreement     — panes of one transition share provenance while samples differ (not pixels).
  permutation   — the provenance multiset is invariant; ordering is NOT certified (canonical-only).
  topology      — add/remove/reorder/duplicate/omit follow the spec list.
  disposable    — the window blob and observer_id reach neither Frame nor canonical.
  staleness     — stale vs current differ by provenance; no synthesised between-state.
  one-way       — full-AST direction-aware guard bites nested authority imports and D_n ingestion.
  differential  — mutating the observer collection (N=0 included) leaves the REAL core byte-identical."""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = os.path.join(ROOT, "tools", "terrain")
if _T not in sys.path:
    sys.path.insert(0, _T)

import chorus as C                                                      # noqa: E402
import kinema as K                                                      # noqa: E402
import gamegen as G                                                     # noqa: E402
import descent as D                                                     # noqa: E402
import move as M                                                        # noqa: E402
import rngstream as R                                                   # noqa: E402
import entity as E                                                      # noqa: E402
import actionlog as A                                                   # noqa: E402
import enact as EN                                                      # noqa: E402
import statecanon as SC                                                 # noqa: E402
import rerun as RP                                                      # noqa: E402


def _real_transition(seed, depth):
    """A genuine enact MOVE transition, both ends identified by statecanon — the real (transition, witnesses)
    a Scene is handed."""
    lvl = G.generate(seed, depth)
    up = D.endpoints(lvl)[0]
    for c in ("N", "S", "E", "W"):
        if M.step(lvl, up, c)[0] == M.MOVED:
            s0 = (lvl, up, R.root(seed))
            tok = EN.encode("MOVE", c)
            s1, _o = EN.dispatch(s0, tok)
            dn = SC.d_n(s0[0], E.at(s0[1]), s0[2], A.empty())
            dn1 = SC.d_n(s1[0], E.at(s1[1]), s1[2], A.append(A.empty(), tok))
            return (lvl, up, dn, lvl, s1[1], dn1)
    return None


class Compose(unittest.TestCase):
    def test_repeated_observation_over_corpus(self):
        for s, d in C.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(C.composition_is_repeated_observation(s, d))

    def test_multiplicity_is_a_list_length(self):
        txn = _real_transition(0xC0FFEE, 2)
        for n in (0, 1, 2, 5):
            specs = [C.ObserverSpec(f"o{i}", 0, 6, None) for i in range(n)]
            self.assertEqual(len(C.compose(txn, specs)), n)

    def test_compose_carries_real_witnesses_verbatim(self):
        txn = _real_transition(0xC0FFEE, 2)
        _ln, _pn, dn, _lm, _pm, dn1 = txn
        scene = C.compose(txn, (C.ObserverSpec("main", 3, 6, ("bounds", 0, 0)),))
        st, wn, wm, cls = C.provenance(scene[0])
        self.assertEqual((wn, wm, st), (dn, dn1, 3))


class Agreement(unittest.TestCase):
    def test_panes_agree_on_provenance_not_pixels(self):
        for s, d in C.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(C.panes_of_one_transition_agree_on_provenance(s, d))

    def test_two_sample_rates_same_authority_different_pixels(self):
        txn = _real_transition(0xC0FFEE, 2)
        a = C.compose(txn, (C.ObserverSpec("a", 0, 6, None),))[0]
        b = C.compose(txn, (C.ObserverSpec("b", 0, 144, None),))[0]
        self.assertEqual(C.provenance(a), C.provenance(b))                       # same authority
        self.assertNotEqual([f.refined for f in a[1]], [f.refined for f in b[1]])  # different pixels


class Permutation(unittest.TestCase):
    def test_multiset_invariant_ordering_not_certified(self):
        for s, d in C.SEEDS:
            with self.subTest(seed=s):
                multiset_ok, ordering_differs = C.the_provenance_multiset_is_permutation_invariant(s, d)
                self.assertTrue(multiset_ok)
                self.assertTrue(ordering_differs)   # we deliberately do NOT certify order


class Topology(unittest.TestCase):
    def test_topology_is_a_list_operation(self):
        for s, d in C.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(C.topology_is_a_list_operation(s, d))

    def test_empty_scene_is_pure(self):
        for s, d in C.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(C.the_empty_scene_is_pure(s, d))


class Disposable(unittest.TestCase):
    def test_window_config_is_disposable(self):
        for s, d in C.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(C.the_window_config_is_disposable(s, d))

    def test_a_bad_spec_refuses_typed(self):
        txn = _real_transition(0, 1)
        with self.assertRaises(C.ChorusError) as cm:
            C.compose(txn, (("not", "a", "spec"),))
        self.assertEqual(cm.exception.code, "CHORUS-REFUSE")


class Staleness(unittest.TestCase):
    def test_stale_and_current_differ_by_provenance(self):
        for s, d in C.SEEDS:
            with self.subTest(seed=s):
                self.assertTrue(C.a_stale_and_a_current_pane_differ_by_provenance(s, d))


class OneWay(unittest.TestCase):
    def test_own_source_is_one_way(self):
        self.assertTrue(C.the_membrane_is_one_way())

    def test_guard_bites_nested_authority_import(self):
        self.assertFalse(C._source_is_one_way(
            "import kinema\ndef f(t, s):\n    import enact as _E\n    return _E.dispatch(t, s)\n"))

    def test_guard_bites_d_n_ingestion(self):
        self.assertFalse(C._source_is_one_way(
            "def g(t):\n    import statecanon as _S\n    return _S.d_n(*t)\n"))
        self.assertFalse(C._source_is_one_way("x = y.d_n(1)\n"))

    def test_guard_allows_the_read_only_path(self):
        self.assertTrue(C._source_is_one_way(
            "import kinema\nimport gamegen\nimport descent\n"
            "def h(t, s):\n    return kinema.frames(*t, s.source_tick, s.samples)\n"))

    def test_no_core_module_imports_chorus(self):
        for name in ("gamegen", "descent", "move", "entity", "rngstream", "descend", "loot",
                     "combat", "heirloom", "actionlog", "savegame", "enact", "rerun", "statecanon", "kinema"):
            with open(os.path.join(_T, name + ".py"), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            top = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    top.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    top.add((node.module or "").split(".")[0])
            self.assertNotIn("chorus", top, f"{name} imports chorus (a reverse edge)")


class Differential(unittest.TestCase):
    """The canonical half: mutating the observer collection — N=0 included — leaves the REAL core
    byte-identical. N=0 exercises the core with NO observer/Scene at all."""
    def _core_fingerprint(self):
        # computed by the CORE directly; no chorus involved
        rec, _toks, _f = RP._saved_run(0xABCDE, 3, 3, 2)
        return (SC.statecanon_digest(), RP.rerun_digest(), EN.enact_digest(),
                G.digest_of(0xABCDE, 3), RP.verdict(rec))

    def test_core_runs_identically_regardless_of_observer_topology(self):
        n0 = self._core_fingerprint()                                   # N=0: the core with no observers
        txn = _real_transition(0xABCDE, 3)
        for n in (1, 2, 7, 40):
            specs = [C.ObserverSpec(f"o{i}", i, 144, ("bounds", i, i, 800, 600)) for i in range(n)]
            scene = C.compose(txn, specs)                              # exercise the observer layer
            self.assertEqual(len(scene), n)
            self.assertEqual(self._core_fingerprint(), n0,
                             f"observer topology N={n} perturbed the canonical core")
        # duplicate / reorder / omit also leave the core untouched
        C.compose(txn, [C.ObserverSpec("d", 0, 6, None)] * 5)          # duplicate
        C.compose(txn, [])                                             # omit all (N=0)
        self.assertEqual(self._core_fingerprint(), n0)


class Conformance(unittest.TestCase):
    def test_emitted_matches_pinned(self):
        self.assertTrue(C.emitted_matches_pinned())

    def test_scenes_and_top_reproduce(self):
        for n in C.SCENES:
            self.assertEqual(C.scene_result(n), C.golden(n))
        self.assertEqual(C.chorus_digest(), C.golden("chorus"))

    def test_an_unpinned_name_refuses_typed(self):
        self.assertTrue(C.an_unpinned_name_refuses())
        with self.assertRaises(C.ChorusError) as cm:
            C.golden("not-a-scene")
        self.assertEqual(cm.exception.code, "CHORUS-REFUSE")

    def test_layer_is_view_and_substrate_declared(self):
        self.assertEqual(C.LAYER, "VIEW")
        self.assertEqual(C.ALLOWED_IMPORTS,
                         ("ast", "collections", "hashlib", "os", "gamegen", "descent", "kinema"))


if __name__ == "__main__":
    unittest.main()
