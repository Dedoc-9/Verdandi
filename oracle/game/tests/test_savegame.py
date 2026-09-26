# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `savegame` (URDRSAV1) — the durable serialization of the earned canonical
components; D24 §3's persistence rung (chain role "persist").

The distinguishing claims, each a distinct failure surface:
  round-trip / re-bind — serialize->restore->re-serialize is bit-identical AND yields usable typed objects.
  persist != replay    — the stream is restored DIRECTLY from (n, R_n), never by folding the actionlog.
  regeneration         — the level regenerates from (seed, depth); the record stores no cells.
  framing              — length-framed, so a token that mimics a component encoding round-trips.
  integrity            — every byte flip and truncation refuses; a re-sealed wrong-component refuses.
  isolation            — imports no persist.py / storecost / horizon; one identity mechanism; not the D_n.

Restore is verified against each component's OWN identity authority (gamegen/entity/rngstream/actionlog),
never against savegame's envelope alone."""
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

import savegame as S                                                     # noqa: E402
import gamegen as G                                                     # noqa: E402
import entity as E                                                      # noqa: E402
import rngstream as R                                                   # noqa: E402
import actionlog as A                                                   # noqa: E402


def _mk(seed, depth, pos, tokens, stream_tokens):
    return seed, depth, pos, R.apply(R.root(seed), stream_tokens), A.from_actions(tokens)


class RoundTripAndRebind(unittest.TestCase):
    def test_round_trips_bit_identical(self):
        for c in S.CORPUS:
            with self.subTest(seed=c[0]):
                self.assertTrue(S.a_snapshot_round_trips(*c))

    def test_restore_yields_usable_typed_state(self):
        seed, depth, pos, st, lg = _mk(0xDEADBEEF, 3, (3, 4), ("N", "loot:x"), ("loot:x",))
        s2, d2, level, ent, stream, log = S.restore(S.serialize(seed, depth, pos, st, lg))
        # each reconstructed object matches its OWN authority, independently of savegame
        self.assertEqual(s2, seed)
        self.assertEqual(d2, depth)
        self.assertEqual(G.level_digest(level), G.level_digest(G.generate(seed, depth)))
        self.assertEqual(ent.get("pos"), pos)
        self.assertEqual(E.entity_digest(ent), E.entity_digest(E.at(pos)))
        self.assertEqual(stream, st)
        self.assertEqual(R.stream_digest(stream), R.stream_digest(st))
        self.assertEqual(A.entries(log), A.entries(lg))
        self.assertTrue(all(S.restore_yields_usable_typed_state(*c) for c in S.CORPUS))


class PersistIsNotReplay(unittest.TestCase):
    def test_stream_restored_directly_not_folded(self):
        self.assertTrue(S.persist_is_not_replay(0, 1, (3, 4)))

    def test_a_log_that_folds_to_a_different_stream_still_restores_the_stored_stream(self):
        seed = 7
        log = A.from_actions(("N", "loot:x", "S"))          # non-advancing move mixed in
        stored = R.apply(R.root(seed), ("loot:only",))       # deliberately != folding the log
        folded = R.apply(R.root(seed), A.entries(log))
        self.assertNotEqual(R.stream_digest(stored), R.stream_digest(folded))
        _s, _d, _lvl, _e, stream, _lg = S.restore(S.serialize(seed, 1, (0, 0), stored, log))
        self.assertEqual(stream, stored)                     # the STORED stream, not the fold


class Regeneration(unittest.TestCase):
    def test_level_regenerated_not_stored(self):
        for c in S.CORPUS:
            with self.subTest(seed=c[0]):
                self.assertTrue(S.the_level_is_regenerated_not_stored(*c))

    def test_record_size_is_independent_of_level_dimensions(self):
        # two different (seed, depth) with the SAME log/pos give records of the SAME length
        st = R.root(0)
        lg = A.from_actions(("a", "b"))
        r1 = S.serialize(0, 1, (0, 0), st, lg)
        r2 = S.serialize(12345, 3, (0, 0), R.root(12345), lg)
        self.assertEqual(len(r1), len(r2))


class Framing(unittest.TestCase):
    def test_length_framing_is_unambiguous(self):
        self.assertTrue(S.length_framing_is_unambiguous(0, 1, (2, 2)))

    def test_a_token_mimicking_a_component_encoding_round_trips(self):
        tricky = (b"|n:5|r:deadbeef", b"URDRSAV1", b"")
        log = A.from_actions(tricky)
        _s, _d, _l, _e, _st, log2 = S.restore(S.serialize(0, 1, (1, 1), R.root(0), log))
        self.assertEqual(A.entries(log2), tricky)


class Integrity(unittest.TestCase):
    def test_every_single_byte_flip_refuses(self):
        self.assertTrue(S.every_single_byte_flip_refuses(0, 1, (3, 4)))

    def test_every_truncation_refuses(self):
        self.assertTrue(S.every_truncation_refuses(0, 1, (3, 4)))

    def test_a_resealed_wrong_component_refuses(self):
        self.assertTrue(S.a_resealed_wrong_component_refuses(0, 1, (3, 4)))

    def test_address_is_the_content_digest_and_corrupt_has_none(self):
        rec = S.serialize(0, 1, (3, 4), R.root(0), A.from_actions(("a",)))
        self.assertEqual(S.address(rec), rec[-32:].hex())
        bad = bytearray(rec); bad[0] ^= 0xFF
        with self.assertRaises(S.SavegameError):
            S.address(bytes(bad))


class RefuseDomain(unittest.TestCase):
    def test_serialize_refuses_malformed_components(self):
        st, lg = R.root(0), A.from_actions(("a",))
        for args in ((-1, 1, (3, 4), st, lg), (0, -1, (3, 4), st, lg), (0, 1, (0.0, 0), st, lg),
                     (0, 1, (3, 4), "stream", lg), (0, 1, (3, 4), st, "log"), (0, 1, (3,), st, lg)):
            with self.subTest(args=args):
                with self.assertRaises(S.SavegameError) as cm:
                    S.serialize(*args)
                self.assertEqual(cm.exception.code, "SAVEGAME-REFUSE")

    def test_restore_refuses_malformed_records(self):
        for bad in (None, 0, b"short", b"X" * 400):
            with self.subTest(rec=bad):
                with self.assertRaises(S.SavegameError) as cm:
                    S.restore(bad)
                self.assertEqual(cm.exception.code, "SAVEGAME-REFUSE")

    def test_refuse_is_total(self):
        self.assertEqual(S.refuse_is_total(), (True, True))


class Isolation(unittest.TestCase):
    def test_imports_no_persist_or_mmo_arc(self):
        top = self._mod_scope_imports("savegame.py")
        self.assertEqual(top, set(S.ALLOWED_IMPORTS))
        self.assertEqual(top, {"hashlib", "os", "gamegen", "entity", "rngstream", "actionlog"})
        allimp = self._imports("savegame.py")
        for banned in ("persist", "storecost", "horizon"):
            self.assertNotIn(banned, allimp)

    def test_one_identity_mechanism_and_not_persist(self):
        self.assertTrue(S.does_not_import_persist_or_mint_identity())

    def test_is_not_the_assembled_canonical_state(self):
        self.assertTrue(S.is_not_the_assembled_canonical_state())
        for banned in ("canonical_state", "d_n", "statecanon", "assembled_digest"):
            self.assertFalse(hasattr(S, banned))

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(S.LAYER, "CORE")
        self.assertIn("canonical game state", S.D24_ANSWER)

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


class DeterminismAndRecord(unittest.TestCase):
    def test_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import savegame as S; "
                "print('|'.join(S.scene_result(n) for n in S.SCENES))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)

    def test_scenes_match_their_goldens(self):
        for n in S.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(S.scene_result(n), S.golden(n))
        self.assertEqual(S.savegame_digest(), S.golden("savegame"))
        self.assertTrue(S.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(S.an_unpinned_name_refuses())
        with self.assertRaises(S.SavegameError):
            S.golden("wishful")


if __name__ == "__main__":
    unittest.main()
