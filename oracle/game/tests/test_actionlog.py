# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Daniel J. Dillberg
"""Red-first falsifiers for `actionlog` (URDRACT1) — the authoritative recoverable action history.

The distinguishing claims, each a distinct failure surface:
  recoverability  — entries return the exact appended order (a stream cannot).
  order-commit    — [A,B] and [B,A] commit to different states; str/bytes equivalence does not.
  compose-not-dup — the digest IS rngstream's fold from a declared root; append is one rngstream.advance.
  external ruler  — folding the log through a RUN seed reproduces that run's stream (checked against
                    rngstream, an authority actionlog does not own), and a reorder diverges it.
  opacity         — tokens are opaque; no move/entity import.

The order property is verified against rngstream directly, never against actionlog's own digest alone."""
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

import actionlog as A                                                     # noqa: E402
import rngstream as R                                                     # noqa: E402


def _canon(x):
    return x if isinstance(x, bytes) else x.encode("utf-8")


class Recoverability(unittest.TestCase):
    def test_entries_recover_the_appended_order(self):
        for seq in A.CORPUS:
            with self.subTest(seq=seq):
                self.assertEqual(A.entries(A.from_actions(seq)), tuple(_canon(x) for x in seq))

    def test_count_is_the_length(self):
        self.assertEqual(A.count(A.empty()), 0)
        self.assertEqual(A.count(A.from_actions(("N", "S", "E"))), 3)

    def test_a_stream_cannot_recover_but_a_log_can(self):
        # the whole point: the log holds the actions; rngstream's Stream does not expose them
        log = A.from_actions(("a", "b", "c"))
        self.assertEqual(A.entries(log), (b"a", b"b", b"c"))
        self.assertFalse(hasattr(A.stream_of(log), "actions"))


class OrderCommitment(unittest.TestCase):
    def test_reorder_changes_the_committed_state(self):
        # [A,B] != [B,A] for distinct actions — the explicit reorder witness
        self.assertNotEqual(A.digest(A.from_actions(("A", "B"))),
                            A.digest(A.from_actions(("B", "A"))))
        self.assertTrue(A.a_reorder_changes_the_committed_state("A", "B"))
        self.assertTrue(A.a_reorder_changes_the_committed_state("N", b"loot:x"))

    def test_str_bytes_equivalence_does_not_change_state(self):
        self.assertEqual(A.digest(A.append(A.empty(), "N")), A.digest(A.append(A.empty(), b"N")))
        self.assertEqual(A.from_actions(("N", "S")), A.from_actions((b"N", b"S")))
        self.assertTrue(A.str_and_bytes_are_the_same_action())

    def test_append_is_immutable(self):
        base = A.append(A.empty(), "N")
        _ = A.append(base, "S")
        self.assertEqual(base, (b"N",))
        self.assertTrue(A.append_is_immutable_and_order_sensitive())

    def test_empty_log_identity(self):
        self.assertEqual(A.count(A.empty()), 0)
        self.assertEqual(A.digest(A.empty()), R.stream_digest(A.LOG_ROOT))
        self.assertTrue(A.the_empty_log_has_a_canonical_identity())


class ComposeNotDuplicate(unittest.TestCase):
    def test_digest_is_rngstreams_fold_from_the_declared_root(self):
        for seq in A.CORPUS:
            with self.subTest(seq=seq):
                log = A.from_actions(seq)
                expected = R.stream_digest(R.apply(A.LOG_ROOT, A.entries(log)))
                self.assertEqual(A.digest(log), expected)

    def test_each_append_is_exactly_one_advance(self):
        log = A.from_actions(("N", b"loot:x"))
        self.assertEqual(A.stream_of(A.append(log, "S")),
                         R.advance(A.stream_of(log), b"S"))
        for seq in A.CORPUS:
            with self.subTest(seq=seq):
                self.assertTrue(A.each_append_is_one_advance(A.from_actions(seq), "Z"))

    def test_log_root_is_seed_independent_and_domain_separated(self):
        # not a run seed's root, and not rngstream's own root of any small seed
        self.assertEqual(A.LOG_ROOT.n, 0)
        for seed in (0, 1, 12345):
            self.assertNotEqual(A.LOG_ROOT.r, R.root(seed).r)

    def test_the_ordering_builds_no_second_chain(self):
        self.assertTrue(A.the_ordering_builds_no_second_chain())


class TheExternalRuler(unittest.TestCase):
    """Order certified against rngstream — an authority actionlog does not own — never its own digest."""

    def test_the_log_reproduces_a_run_stream(self):
        for seed, acts in A.AGREE:
            with self.subTest(seed=seed):
                self.assertTrue(A.the_log_reproduces_a_run_stream(seed, acts))
                # and directly: folding the log's entries through the run seed == folding the raw actions
                log = A.from_actions(acts)
                self.assertEqual(R.stream_digest(R.apply(R.root(seed), A.entries(log))),
                                 R.stream_digest(R.apply(R.root(seed), tuple(_canon(a) for a in acts))))

    def test_a_reordered_log_diverges_the_run_stream(self):
        # order is caught by the STREAM, not by actionlog's own digest
        seed = 0xDEADBEEF
        fwd = R.stream_digest(R.apply(R.root(seed), (b"loot:x", b"loot:y")))
        rev = R.stream_digest(R.apply(R.root(seed), (b"loot:y", b"loot:x")))
        self.assertNotEqual(fwd, rev)
        for seed, acts in A.AGREE:
            with self.subTest(seed=seed):
                self.assertTrue(A.a_reordered_log_diverges_the_run_stream(seed, acts))

    def test_not_claimed_a_unique_preimage(self):
        # honesty guard: the module exposes no "preimage"/"invert" API — only reproduction
        self.assertFalse(hasattr(A, "preimage"))
        self.assertFalse(hasattr(A, "invert"))


class Opacity(unittest.TestCase):
    def test_tokens_are_opaque_no_move_or_entity_import(self):
        top = self._mod_scope_imports("actionlog.py")
        self.assertEqual(top, set(A.ALLOWED_IMPORTS))
        self.assertEqual(top, {"hashlib", "os", "rngstream"})
        self.assertNotIn("move", self._imports("actionlog.py"))
        self.assertNotIn("entity", self._imports("actionlog.py"))

    def test_rngstream_does_not_depend_on_actionlog(self):
        self.assertTrue(A.rngstream_does_not_depend_on_actionlog())
        self.assertNotIn("actionlog", self._imports("rngstream.py"))

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


class TheRefuseDomain(unittest.TestCase):
    def test_malformed_action_refuses_typed(self):
        for bad in (0, None, ("v",), 1.0, [1]):
            with self.subTest(action=bad):
                with self.assertRaises(A.ActionlogError) as cm:
                    A.append(A.empty(), bad)
                self.assertEqual(cm.exception.code, "ACTIONLOG-REFUSE")

    def test_malformed_log_refuses_typed(self):
        for bad in (None, 0, "log", [b"x"], (b"ok", "notbytes")):
            with self.subTest(log=bad):
                with self.assertRaises(A.ActionlogError) as cm:
                    A.digest(bad)
                self.assertEqual(cm.exception.code, "ACTIONLOG-REFUSE")

    def test_refuse_is_total(self):
        self.assertEqual(A.refuse_is_total(), (True, True))


class DeterminismAndRecord(unittest.TestCase):
    def test_pure_across_fresh_interpreters(self):
        code = ("import sys; sys.path.insert(0, %r); import actionlog as A; "
                "print('|'.join(A.scene_result(n) for n in A.SCENES))" % _T)
        outs = []
        for hs in ("0", "1", "2"):
            env = dict(os.environ, PYTHONHASHSEED=hs, PYTHONUTF8="1")
            r = subprocess.run([sys.executable, "-c", code], env=env, capture_output=True,
                               text=True, timeout=180)
            self.assertEqual(r.returncode, 0, r.stderr)
            outs.append(r.stdout.strip())
        self.assertEqual(len(set(outs)), 1, outs)

    def test_the_layer_is_declared_as_data(self):
        self.assertEqual(A.LAYER, "CORE")
        self.assertIn("canonical game state", A.D24_ANSWER)

    def test_scenes_match_their_goldens(self):
        for n in A.SCENES:
            with self.subTest(scene=n):
                self.assertEqual(A.scene_result(n), A.golden(n))
        self.assertEqual(A.actionlog_digest(), A.golden("actionlog"))
        self.assertTrue(A.emitted_matches_pinned())

    def test_an_unpinned_name_refuses(self):
        self.assertTrue(A.an_unpinned_name_refuses())
        with self.assertRaises(A.ActionlogError):
            A.golden("wishful")


if __name__ == "__main__":
    unittest.main()
