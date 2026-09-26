# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `statecanon` (URDRSTC1) — the assembled canonical identity `D_n` over the four
earned component identities. The fourteenth game-layer vertical slice and D24 §2's assembled-state rung; it
COMPOSES `gamegen`/`entity`/`rngstream`/`actionlog` identities and mints exactly one new digest.

The distinguishing claims, each a distinct failure surface:
  compose     — D_n equals SHA-256 of the labelled preimage built independently from the four public digests.
  load-bearing— mutating ANY one of the four components moves D_n; none is vestigial.
  history     — same (level, entity, stream), different history -> different D_n (the ratified choice).
  identity    — D_n depends on the component identities, not on object instances.
  view        — a view-only field cannot enter `entity`, so it cannot reach D_n.
  framing     — the labelled fixed-width `|`-delimited preimage is injective (a swap changes it).
  structure   — the assembly composes the four authorities and mints ONE sha256 (AST); a bypass mutant reddens.
  ownership   — statecanon exposes no savegame/rerun API and imports neither (none absorbs another)."""
import ast
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_T = os.path.join(ROOT, "tools", "terrain")
if _T not in sys.path:
    sys.path.insert(0, _T)

import statecanon as SC                                                 # noqa: E402
import gamegen as G                                                     # noqa: E402
import entity as E                                                      # noqa: E402
import rngstream as R                                                   # noqa: E402
import actionlog as A                                                   # noqa: E402


def _guard_on(src):
    """The AST composition guard re-evaluated on an arbitrary source string — so the falsifier can be shown
    to FAIL on a bypass mutant, not merely pass on the honest source."""
    tree = ast.parse(src)
    assembly = [n for n in tree.body
                if isinstance(n, ast.FunctionDef) and n.name in ("d_n", "d_n_preimage")]
    if len(assembly) != 2:
        return False
    attrs = [a.attr for fn in assembly for a in ast.walk(fn) if isinstance(a, ast.Attribute)]
    identities = {"level_digest", "entity_digest", "stream_digest", "digest"}
    one_sha = attrs.count("sha256") == 1
    no_reimpl = not ({"canon_bytes", "entity_bytes", "stream_bytes", "stream_of"} & set(attrs))
    top = set()
    for node in tree.body:
        if isinstance(node, ast.Import):
            top.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            top.add((node.module or "").split(".")[0])
    imports_clean = (top == set(SC.ALLOWED_IMPORTS)
                     and not ({"savegame", "rerun", "lockstep"} & top))
    return (identities <= set(attrs) and one_sha and no_reimpl
            and "advance" not in attrs and imports_clean)


class Compose(unittest.TestCase):
    def test_d_n_is_the_composition_across_the_corpus(self):
        for c in SC.CORPUS:
            with self.subTest(seed=c[0]):
                self.assertTrue(SC.d_n_is_the_composition_of_the_four_identities(*c))

    def test_d_n_equals_the_independent_recomputation(self):
        import hashlib
        level, ent, stream, log = SC._state(0xC0FFEE, 2, (5, 6), ("E", "loot:a"), ("loot:a",))
        want = hashlib.sha256(b"%s|lvl:%s|ent:%s|rng:%s|log:%s" % (
            SC.MAGIC, G.level_digest(level).encode(), E.entity_digest(ent).encode(),
            R.stream_digest(stream).encode(), A.digest(log).encode())).hexdigest()
        self.assertEqual(SC.d_n(level, ent, stream, log), want)


class LoadBearing(unittest.TestCase):
    def test_each_component_moves_d_n(self):
        for c in SC.CORPUS:
            with self.subTest(seed=c[0]):
                self.assertTrue(SC.each_component_moves_d_n(*c))

    def test_a_shared_component_is_not_ignored(self):
        # a genuine red-first: if any component were dropped from the preimage this equality would hold
        level, ent, stream, log = SC._state(0, 1, (3, 4), ("N",), ())
        moved_entity = SC.d_n(level, E.at((99, 99)), stream, log)
        self.assertNotEqual(SC.d_n(level, ent, stream, log), moved_entity)


class History(unittest.TestCase):
    def test_history_is_in_the_identity(self):
        self.assertTrue(SC.history_is_in_the_identity(0, 1, (3, 4)))

    def test_same_world_entity_stream_different_history_differs(self):
        level, ent, stream = G.generate(7, 2), E.at((1, 1)), R.root(7)
        a = SC.d_n(level, ent, stream, A.from_actions(("N", "S")))
        b = SC.d_n(level, ent, stream, A.from_actions(("S", "N")))
        self.assertNotEqual(a, b)


class IdentityNotInstance(unittest.TestCase):
    def test_depends_only_on_identity(self):
        for c in SC.CORPUS:
            with self.subTest(seed=c[0]):
                self.assertTrue(SC.d_n_depends_only_on_identity(*c))


class ViewBoundary(unittest.TestCase):
    def test_a_view_field_cannot_reach_d_n(self):
        self.assertTrue(SC.a_view_field_cannot_reach_d_n())

    def test_entity_refuses_the_view_field(self):
        with self.assertRaises(E.EntityError):
            E.Entity(pos=(0, 0), facing="N")


class Framing(unittest.TestCase):
    def test_framing_is_injective(self):
        for s, d, p, _l, _st in SC.CORPUS:
            with self.subTest(seed=s):
                self.assertTrue(SC.the_framing_is_injective(s, d, p))

    def test_component_digests_are_64_hex_without_delimiter(self):
        level, ent, stream, log = SC._state(0, 1, (2, 2), ("N",), ("loot:a",))
        for dig in (G.level_digest(level), E.entity_digest(ent),
                    R.stream_digest(stream), A.digest(log)):
            self.assertEqual(len(dig), 64)
            self.assertNotIn("|", dig)


class Structure(unittest.TestCase):
    def test_the_assembly_composes_the_four_authorities(self):
        self.assertTrue(SC.the_assembly_composes_the_four_authorities())

    def test_the_guard_reddens_on_a_bypass_that_reproduces_d_n(self):
        # THE USER'S REQUIREMENT, made a red-first test: a mutant that inlines a component's own
        # sha256(preimage) produces the SAME D_n but must redden on the structure (a second sha256, and it
        # reaches canon_bytes). The falsifier CAN fail.
        with open(os.path.join(_T, "statecanon.py"), encoding="utf-8") as fh:
            honest = fh.read()
        self.assertTrue(_guard_on(honest))                                     # honest source passes
        inlined = honest.replace("_G.level_digest(level).encode(),",
                                 "hashlib.sha256(_G.canon_bytes(level)).hexdigest().encode(),", 1)
        self.assertFalse(_guard_on(inlined))                                   # same D_n, but reddens
        dropped = honest.replace("        _A.digest(log).encode(),\n    )", "    )")
        self.assertFalse(_guard_on(dropped))                                   # drops an authority
        imported = honest.replace("import actionlog as _A",
                                  "import actionlog as _A\nimport savegame as _SV", 1)
        self.assertFalse(_guard_on(imported))                                  # absorbs a neighbour

    def test_exactly_one_sha256_in_the_assembly(self):
        with open(os.path.join(_T, "statecanon.py"), encoding="utf-8") as fh:
            honest = fh.read()
        tree = ast.parse(honest)
        assembly = [n for n in tree.body
                    if isinstance(n, ast.FunctionDef) and n.name in ("d_n", "d_n_preimage")]
        attrs = [a.attr for fn in assembly for a in ast.walk(fn) if isinstance(a, ast.Attribute)]
        self.assertEqual(attrs.count("sha256"), 1)


class Ownership(unittest.TestCase):
    def test_statecanon_absorbs_no_neighbor(self):
        self.assertTrue(SC.statecanon_absorbs_no_neighbor())

    def test_no_savegame_or_rerun_api(self):
        for nm in ("serialize", "restore", "address", "replay", "verdict", "reconstruct_origin"):
            self.assertFalse(hasattr(SC, nm))

    def test_imports_are_exactly_the_declared_substrate(self):
        self.assertEqual(SC.ALLOWED_IMPORTS,
                         ("hashlib", "os", "gamegen", "entity", "rngstream", "actionlog"))


class Conformance(unittest.TestCase):
    def test_emitted_matches_pinned(self):
        self.assertTrue(SC.emitted_matches_pinned())

    def test_scenes_and_top_reproduce(self):
        for n in SC.SCENES:
            self.assertEqual(SC.scene_result(n), SC.golden(n))
        self.assertEqual(SC.statecanon_digest(), SC.golden("statecanon"))

    def test_an_unpinned_name_refuses_typed(self):
        self.assertTrue(SC.an_unpinned_name_refuses())
        with self.assertRaises(SC.StatecanonError) as cm:
            SC.golden("not-a-scene")
        self.assertEqual(cm.exception.code, "STATECANON-REFUSE")


if __name__ == "__main__":
    unittest.main()
