# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `entity` (URDRETY1) — the canonical entity, a content-addressed
component in ONE identity vocabulary.

  ONE VOCABULARY, NOT TWO. `move` names the entity by `entity.entity_digest`, the way it names the
    level by `gamegen.level_digest`; its state bytes carry `|ent:<digest>` and NO inline `pos:x,y`,
    so `statecanon` will compose the entity the same way it composes the level and nothing needs
    translating. The position `move` spawns is the position the record holds.
  EQUAL FIELDS ARE THE SAME ENTITY: equal declared fields give equal digests; a change in any field
    moves it. The digest is a function of the DECLARED field vocabulary, walked in declared order.
  ONLY POSITION IS EARNED, and the record says so — `FIELDS == ("pos",)`. An undeclared keyword and
    a malformed position each REFUSE typed (ENTITY-REFUSE), which is what keeps a view-only quantity
    (a facing for animation, an interpolated sub-cell position) out of canonical identity.
  FORWARD-COMPATIBLE, so growth costs no re-mint: a later field appends as `|key:value` and leaves
    the `pos:x,y` bytes byte-identical.
  THE RECORD DEPENDS ON NOTHING UNDER tools/: its declared substrate is stdlib (`hashlib`, `os`);
    only the scene corpus reaches for `gamegen`/`descent`, LAZILY, so the dependency is not a
    module-load coupling and it runs one way.

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

import entity as E                                                        # noqa: E402
import move as M                                                          # noqa: E402
import gamegen as G                                                       # noqa: E402
import descent as D                                                       # noqa: E402

POS = (3, 4)


class EqualFieldsAreTheSameEntity(unittest.TestCase):
    def test_equal_declared_fields_have_equal_digests(self):
        self.assertEqual(E.entity_digest(E.at(POS)), E.entity_digest(E.at((3, 4))))
        self.assertEqual(E.digest_at(POS), E.digest_at((3, 4)))

    def test_a_change_in_position_moves_the_digest(self):
        self.assertNotEqual(E.digest_at(POS), E.digest_at((POS[0] + 1, POS[1])))
        self.assertNotEqual(E.digest_at(POS), E.digest_at((POS[0], POS[1] + 1)))

    def test_the_law_holds_over_the_corpus_spawns(self):
        for s, d in G.CORPUS:
            p = D.endpoints(G.generate(s, d))[0]
            with self.subTest(seed=s, depth=d):
                self.assertTrue(E.equal_fields_are_the_same_entity(p))

    def test_the_canonical_bytes_are_magic_then_declared_fields(self):
        self.assertEqual(E.entity_bytes(E.at(POS)), b"URDRETY1|pos:3,4")
        self.assertTrue(E.entity_bytes(E.at(POS)).startswith(E.MAGIC))


class OnlyPositionIsDeclared(unittest.TestCase):
    def test_the_field_set_is_exactly_what_is_earned(self):
        self.assertEqual(E.FIELDS, ("pos",))
        self.assertTrue(E.only_position_is_declared())

    def test_every_declared_field_has_a_serializer(self):
        self.assertEqual(set(E._SERIALIZERS), set(E.FIELDS))

    def test_an_undeclared_field_refuses_typed(self):
        """A view-only or not-yet-earned field cannot enter the record — the constructor refuses it
        typed, which is what keeps a facing-for-animation or an interpolated position OUT of the
        canonical digest."""
        for bad in ("facing", "camera", "hp", "interp", "sprite"):
            with self.subTest(field=bad):
                with self.assertRaises(E.EntityError) as cm:
                    E.Entity(pos=(0, 0), **{bad: 1})
                self.assertEqual(cm.exception.code, "ENTITY-REFUSE")
        self.assertTrue(E.an_undeclared_field_refuses())

    def test_a_missing_field_refuses_typed(self):
        with self.assertRaises(E.EntityError) as cm:
            E.Entity()
        self.assertEqual(cm.exception.code, "ENTITY-REFUSE")

    def test_a_malformed_position_refuses_typed(self):
        for bad in ((0.0, 0), (0,), ("0", 0), [0, 0], None, (0, 0, 0), (True, 0)):
            with self.subTest(pos=bad):
                with self.assertRaises(E.EntityError) as cm:
                    E.at(bad)
                self.assertEqual(cm.exception.code, "ENTITY-REFUSE")
        self.assertTrue(E.a_malformed_position_refuses())


class ForwardCompatible(unittest.TestCase):
    def test_a_new_field_does_not_reformat_the_position(self):
        """THE FORWARD-COMPATIBILITY PROOF, so a later rung earning a field costs no re-mint of what
        is pinned: the `pos:x,y` segment is byte-identical under extension, and a new field only
        APPENDS a `|key:value` segment."""
        unchanged, appended = E.a_new_field_does_not_reformat_position(POS)
        self.assertTrue(unchanged, "extending FIELDS reformatted the position segment")
        self.assertTrue(appended, "a new field did not append a segment")

    def test_the_position_segment_is_stable_against_todays_bytes(self):
        base = E.entity_bytes(E.at(POS))
        self.assertEqual(base, E.MAGIC + b"|" + b"pos:%d,%d" % POS)


class TheFieldsAreWalkedInDeclaredOrder(unittest.TestCase):
    def test_the_walk_follows_FIELDS_not_insertion_or_hash_order(self):
        self.assertTrue(E.the_fields_are_walked_in_declared_order())
        b = E.entity_bytes(E.at(POS))
        self.assertTrue(b.startswith(E.MAGIC + b"|" + E._SERIALIZERS[E.FIELDS[0]](POS)))


class OneVocabularyThroughMove(unittest.TestCase):
    """THE ONE-VOCABULARY SLICE, the property `move`'s refactor exists to hold: `move` names the
    entity by its digest, exactly as it names the level, so there is no second serialization of the
    entity for `statecanon` to reconcile."""

    def test_move_names_the_entity_by_its_digest_not_an_inline_position(self):
        lv = G.generate(*M.CORPUS[0])
        p = M.spawn(lv)
        sb = M.state_bytes(lv, p)
        self.assertTrue(sb.startswith(b"URDRMOV1|lvl:"))
        self.assertIn(b"|ent:" + E.digest_at(p).encode(), sb)
        self.assertNotIn(b"|pos:", sb)

    def test_the_spawn_move_carries_is_the_position_the_record_holds(self):
        lv = G.generate(*M.CORPUS[0])
        p = M.spawn(lv)
        self.assertEqual(E.at(p).get("pos"), p)
        self.assertIn(E.entity_digest(E.at(p)).encode(), M.state_bytes(lv, p))

    def test_a_moved_step_moves_the_entity_digest_a_blocked_step_does_not(self):
        lv = G.generate(*M.CORPUS[0])
        p = M.spawn(lv)
        for c in M.DIRECTIONS:
            outcome, nxt = M.step(lv, p, c)
            with self.subTest(cmd=c, outcome=outcome):
                if outcome == M.MOVED:
                    self.assertNotEqual(E.digest_at(p), E.digest_at(nxt))
                else:
                    self.assertEqual(E.digest_at(p), E.digest_at(nxt))


class TheRecord(unittest.TestCase):
    def test_scenes_match_their_goldens(self):
        for n in E.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(E.scene_result(n), E.golden(n))
        self.assertEqual(E.entity_digest_scene(), E.golden("entity-digest"))
        self.assertTrue(E.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(E.an_unpinned_name_refuses())
        with self.assertRaises(E.EntityError):
            E.golden("wishful")

    def test_an_unknown_scene_refuses_typed(self):
        with self.assertRaises(E.EntityError) as cm:
            E.scene_case("not-a-scene")
        self.assertEqual(cm.exception.code, "ENTITY-REFUSE")


class DeterminismAndLayer(unittest.TestCase):
    def test_the_digest_is_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import entity as E; "
                "print('|'.join(E.digest_at((x, x + 1)) for x in range(4)))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)

    def test_the_record_substrate_is_declared_stdlib_at_module_scope(self):
        """The entity RECORD depends on nothing under tools/: its module-scope imports are exactly
        `ALLOWED_IMPORTS`, which is standard library only. The scene corpus's `gamegen`/`descent`
        imports are LAZY (function-local), so they are not a load-time coupling — asserted below."""
        top = self._mod_scope_imports("entity.py")
        self.assertEqual(top, set(E.ALLOWED_IMPORTS))
        self.assertEqual(top, {"hashlib", "os"})
        stdlib = getattr(sys, "stdlib_module_names", top)
        self.assertTrue(top <= set(stdlib))

    def test_the_scene_corpus_reaches_for_levels_only_lazily(self):
        """gamegen and descent are imported INSIDE a function, never at module scope — the record
        does not couple to them at load, and an AST walk proves it: they are in the full import set
        but not in the module-scope set."""
        top = self._mod_scope_imports("entity.py")
        allimp = self._all_imports("entity.py")
        for name in ("gamegen", "descent"):
            self.assertIn(name, allimp)
            self.assertNotIn(name, top)

    def test_the_dependency_runs_one_way(self):
        """`move` imports `entity` (it consumes the component); `entity` does not import `move`, and
        neither `gamegen` nor `descent` imports `entity`. The component is named by its consumers,
        it does not know them."""
        self.assertIn("entity", self._all_imports("move.py"))
        self.assertNotIn("move", self._all_imports("entity.py"))
        self.assertNotIn("entity", self._all_imports("gamegen.py"))
        self.assertNotIn("entity", self._all_imports("descent.py"))

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(E.LAYER, "CORE")
        self.assertIn("canonical game state", E.D24_ANSWER)

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
        for node in tree.body:                       # module scope only — skip function/class bodies
            if isinstance(node, ast.Import):
                found.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom):
                found.add((node.module or "").split(".")[0])
        return found


if __name__ == "__main__":
    unittest.main()
