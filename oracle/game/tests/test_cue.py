# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `cue` (URDRCUE1) — the one-way input membrane: a raw window/device event becomes
a typed `enact` token. WINDOW-1 of the observer-composition arc; the input-side mirror of `chorus`.

Invariant under test: FOCUS IDENTITY IS NON-AUTHORITATIVE; THE CANONICAL ACTION STREAM IS DETERMINED BY THE
INPUT, NOT BY WHICH WINDOW ORIGINATED IT.

Distinct failure surfaces:
  binding       — bind is a pure, real map; the token vocabulary is enact's; the table is data.
  focus         — focus identity alone is non-authoritative (rerouted focus, same keys → same tokens).
  configuration — a different binding table may change the tokens (real map; not focus authority).
  refusal       — three tiers: CUE-REFUSE (ours), ENACT-REFUSE (codec), DESCEND-REFUSE (authority, downstream).
  one-way       — full-AST direction-aware guard: enact codec only, no dispatch/apply/d_n/step, positive control.
  differential  — against a REAL enact/savegame/rerun core, rerouted focus replays byte-identically."""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = os.path.join(ROOT, "tools", "terrain")
if _T not in sys.path:
    sys.path.insert(0, _T)

import cue as C                                                         # noqa: E402
import enact as EN                                                     # noqa: E402
import gamegen as G                                                    # noqa: E402
import descent as D                                                    # noqa: E402
import move as M                                                       # noqa: E402
import rngstream as R                                                  # noqa: E402
import actionlog as A                                                  # noqa: E402
import savegame as SV                                                  # noqa: E402
import rerun as RP                                                     # noqa: E402


def _record_from_tokens(seed, depth, tokens):
    """Build the SAME kind of saved record `rerun` builds, but from a cue-produced token stream — applied
    through the REAL `enact` dispatch and stored by the REAL `savegame`."""
    origin = RP._spawn_origin(seed, depth)
    (lvl, pos, strm), _infos = EN.apply(origin, tokens)
    return SV.serialize(seed, lvl.depth, pos, strm, A.from_actions(tokens))


class Binding(unittest.TestCase):
    def test_every_default_key_binds_to_a_valid_token(self):
        for key, (kind, payload) in C.DEFAULT_BINDINGS:
            tok = C.bind(C.Event("_", key))
            self.assertEqual(EN.decode(tok), (kind, payload))

    def test_bind_is_pure_in_the_event_and_ignores_focus(self):
        for key, _v in C.DEFAULT_BINDINGS:
            self.assertTrue(C.bind_ignores_focus(key))

    def test_the_binding_table_is_data(self):
        self.assertTrue(C.the_binding_table_is_data())

    def test_bind_reads_no_canonical_state(self):
        # sealed observer: bind's signature takes only (event, bindings) — no level/pos/stream/D_n channel
        import inspect
        params = list(inspect.signature(C.bind).parameters)
        self.assertEqual(params, ["event", "bindings"])


class FocusIndependence(unittest.TestCase):
    def test_focus_identity_alone_is_non_authoritative(self):
        tokens_identical, routes_differ, both_used = C.focus_identity_is_non_authoritative()
        self.assertTrue(tokens_identical)   # same keys, rerouted focus → same tokens
        self.assertTrue(routes_differ)      # the reroute is real
        self.assertTrue(both_used)          # each route uses more than one focus (non-vacuous)

    def test_a_third_focus_route_agrees_too(self):
        keys = C._KEYS
        fa = C._FOCUS_A
        fc = tuple("wC" for _ in keys)                 # a single-window route
        self.assertEqual(C.bind_stream(C.route(keys, fa)), C.bind_stream(C.route(keys, fc)))


class Configuration(unittest.TestCase):
    def test_a_different_table_changes_the_tokens(self):
        tokens_differ, both_moves, dirs_differ = C.a_different_binding_table_changes_the_tokens()
        self.assertTrue(tokens_differ)      # configuration CAN change a token …
        self.assertTrue(both_moves)
        self.assertTrue(dirs_differ)        # … which is not focus authority


class Refusal(unittest.TestCase):
    def test_unbound_event_is_cue_refuse(self):
        with self.assertRaises(C.CueError) as cm:
            C.bind(C.Event("wA", "\x00-no-such-key"))
        self.assertEqual(cm.exception.code, "CUE-REFUSE")

    def test_malformed_event_is_cue_refuse(self):
        self.assertTrue(C.a_malformed_event_is_our_refusal())
        with self.assertRaises(C.CueError) as cm:
            C.bind(("wA", "Up"))            # a bare tuple is NOT an Event
        self.assertEqual(cm.exception.code, "CUE-REFUSE")

    def test_bad_payload_is_enact_refuse_not_ours(self):
        self.assertTrue(C.a_bad_payload_surfaces_enacts_refusal())
        with self.assertRaises(EN.EnactError) as cm:
            C.bind(C.Event("w", "Q"), (("Q", (EN.MOVE, "NOPE")),))
        self.assertEqual(cm.exception.code, "ENACT-REFUSE")

    def test_refuse_is_total(self):
        self.assertTrue(C.refuse_is_total())


class OneWay(unittest.TestCase):
    def test_own_source_is_one_way(self):
        self.assertTrue(C.the_membrane_is_one_way())

    def test_guard_bites_dispatch_and_apply(self):
        self.assertFalse(C._source_is_one_way(
            "import enact as _E\ndef f(s, t):\n    return _E.dispatch(s, t)\n"))
        self.assertFalse(C._source_is_one_way(
            "import enact as _E\ndef g(s, t):\n    return _E.apply(s, t)\n"))

    def test_guard_bites_authority_imports_and_d_n(self):
        self.assertFalse(C._source_is_one_way(
            "import enact\ndef h(t):\n    import statecanon as _S\n    return _S.d_n(*t)\n"))
        self.assertFalse(C._source_is_one_way(
            "import enact\ndef k(l, p, c):\n    import move as _M\n    return _M.step(l, p, c)\n"))
        self.assertFalse(C._source_is_one_way("x = y.d_n(1)\n"))

    def test_guard_allows_the_read_only_codec_path(self):
        self.assertTrue(C._source_is_one_way(
            "import enact\ndef h(key):\n    k, p = enact.decode(enact.encode('LOOT'))\n    return k\n"))

    def test_no_core_module_imports_cue(self):
        for name in ("gamegen", "descent", "move", "entity", "rngstream", "descend", "loot",
                     "combat", "heirloom", "actionlog", "savegame", "enact", "rerun", "statecanon",
                     "kinema", "chorus"):
            with open(os.path.join(_T, name + ".py"), encoding="utf-8") as fh:
                tree = ast.parse(fh.read())
            top = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    top.update(a.name.split(".")[0] for a in node.names)
                elif isinstance(node, ast.ImportFrom):
                    top.add((node.module or "").split(".")[0])
            self.assertNotIn("cue", top, f"{name} imports cue (a reverse edge)")


class Differential(unittest.TestCase):
    """The canonical + downstream halves against a REAL core: a rerouted-focus token stream replays
    byte-identically, and a valid-but-illegal token is refused DOWNSTREAM by the authority, not by cue."""
    SEED, DEPTH = 0xABCDE, 3

    def test_rerouted_focus_replays_byte_identically(self):
        rec0, toks, _f = RP._saved_flat_run(self.SEED, self.DEPTH, 4, 2)   # a legal single-floor run
        inv = {C.bind(C.Event("_", k)): k for k, _v in C.DEFAULT_BINDINGS}
        keys = tuple(inv[t] for t in toks)                                 # raw keys that reproduce the run
        n = len(keys)
        fa = tuple(("wA" if i % 2 == 0 else "wB") for i in range(n))
        fb = tuple(("wB" if i % 2 == 0 else "wA") for i in range(n))       # a genuine reroute
        tokens_a = C.bind_stream(C.route(keys, fa))
        tokens_b = C.bind_stream(C.route(keys, fb))
        self.assertNotEqual(fa, fb)
        self.assertEqual(tokens_a, tokens_b)
        self.assertEqual(tokens_a, tuple(toks))                            # cue reproduces the run
        recA = _record_from_tokens(self.SEED, self.DEPTH, tokens_a)
        recB = _record_from_tokens(self.SEED, self.DEPTH, tokens_b)
        self.assertEqual(recA, recB)                                      # byte-identical canonical replay
        self.assertEqual(recA, rec0)                                       # equals rerun's own record
        self.assertEqual(RP.verdict(recA), RP.verdict(recB))
        self.assertEqual(RP.verdict(recA), RP.verdict(rec0))

    def test_a_valid_but_illegal_token_is_refused_downstream_by_the_authority(self):
        lvl = G.generate(self.SEED, self.DEPTH)
        up, down = D.endpoints(lvl)
        self.assertNotEqual(up, down)                     # spawn is not the down-stairs (so a DESCEND is illegal)
        tok = C.bind(C.Event("wA", ">"))                 # WINDOW-1 happily emits a valid DESCEND token
        self.assertEqual(EN.kind_of(tok), EN.DESCEND)
        with self.assertRaises(Exception) as cm:         # the AUTHORITY refuses it downstream, through enact
            EN.dispatch((lvl, up, R.root(self.SEED)), tok)
        self.assertEqual(getattr(cm.exception, "code", ""), "DESCEND-REFUSE")

    def test_core_fingerprint_unperturbed_by_binding(self):
        import statecanon as SC
        rec, _t, _f = RP._saved_flat_run(self.SEED, self.DEPTH, 4, 2)
        before = (SC.statecanon_digest(), RP.rerun_digest(), EN.enact_digest(),
                  G.digest_of(self.SEED, self.DEPTH), RP.verdict(rec))
        C.bind_stream(C.route(C._KEYS, C._FOCUS_A))       # exercise the membrane
        C.bind_stream(C.route(C._KEYS, C._FOCUS_B))
        after = (SC.statecanon_digest(), RP.rerun_digest(), EN.enact_digest(),
                 G.digest_of(self.SEED, self.DEPTH), RP.verdict(rec))
        self.assertEqual(before, after)


class Composition(unittest.TestCase):
    """Stateless stream composition: binding is a homomorphism over concatenation where the bindings succeed;
    refusal is atomic at the batch boundary; a stateful binder breaks the law (the positive control)."""
    def test_the_law_holds_in_full(self):
        self.assertEqual(C.stream_composition_is_stateless(), (True, True, True, True, True, True))

    def test_homomorphism_over_concatenation(self):
        e1 = C.route(("Up", "g"), ("wA", "wB"))
        e2 = C.route(("Right", "Down"), ("wB", "wA"))
        self.assertEqual(C.bind_stream(list(e1) + list(e2)), C.bind_stream(e1) + C.bind_stream(e2))
        self.assertEqual(C.bind_stream(()), ())                 # empty identity
        self.assertEqual(C.bind_stream(list(e1) + list(e1)), C.bind_stream(e1) + C.bind_stream(e1))  # dup

    def test_refusal_is_atomic_at_the_batch_boundary(self):
        with self.assertRaises(C.CueError) as cm:
            C.bind_stream((C.Event("wA", "Up"), C.Event("wA", "\x00-nope"), C.Event("wA", "g")))
        self.assertEqual(cm.exception.code, "CUE-REFUSE")       # one bad event refuses the WHOLE batch

    def test_stateful_binder_breaks_concatenation(self):
        # POSITIVE CONTROL: the real (stateless) bind distributes; a binder that folds the previous event does not
        e1 = C.route(("Up", "g"), ("wA", "wB"))
        e2 = C.route(("Right", "Down", "g"), ("wB", "wA", "wA"))
        self.assertTrue(C._distributes(lambda: C.bind, e1, e2))
        self.assertFalse(C._distributes(C._stateful_binder, e1, e2))


class Conformance(unittest.TestCase):
    def test_emitted_matches_pinned(self):
        self.assertTrue(C.emitted_matches_pinned())

    def test_scenes_and_top_reproduce(self):
        for n in C.SCENES:
            self.assertEqual(C.scene_result(n), C.golden(n))
        self.assertEqual(C.cue_digest(), C.golden("cue"))

    def test_an_unpinned_name_refuses_typed(self):
        self.assertTrue(C.an_unpinned_name_refuses())
        with self.assertRaises(C.CueError) as cm:
            C.golden("not-a-scene")
        self.assertEqual(cm.exception.code, "CUE-REFUSE")

    def test_layer_is_view_and_substrate_declared(self):
        self.assertEqual(C.LAYER, "VIEW")
        self.assertEqual(C.ALLOWED_IMPORTS, ("ast", "collections", "hashlib", "os", "enact"))


if __name__ == "__main__":
    unittest.main()
