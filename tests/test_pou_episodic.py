"""Tests for agent.pou_episodic (episodic WHY-memory)."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.pou_episodic import (
    episodic_recall,
    record_episode,
    summarize_turn,
)


def _is_ascii(s):
    try:
        s.encode("ascii")
        return True
    except Exception:
        return False


class TestSummarizeTurn(unittest.TestCase):
    def test_shape_contains_parts(self):
        msgs = [{"role": "user", "content": "fix login bug please"}]
        s = summarize_turn(msgs, "done patching auth")
        self.assertIn("fix login bug", s)
        self.assertIn("tools", s)
        self.assertIn("done patching", s)
        self.assertTrue(_is_ascii(s))

    def test_truncation(self):
        msgs = [{"role": "user", "content": "x" * 500}]
        s = summarize_turn(msgs, "y" * 500, max_chars=300)
        self.assertLessEqual(len(s), 300)
        self.assertTrue(_is_ascii(s))

    def test_fallback_on_empty(self):
        s = summarize_turn([], "")
        self.assertEqual(s, "quiet turn")

    def test_ascii_only_unicode(self):
        msgs = [{"role": "user", "content": "caf\u00e9 \u0394 \U0001f600 hello"}]
        s = summarize_turn(msgs, "r\u00e9ponse \U0001f680 ok")
        self.assertTrue(_is_ascii(s))
        self.assertTrue(len(s) > 0)

    def test_non_string_messages(self):
        s = summarize_turn([None, "x", 42], "ok")
        self.assertTrue(_is_ascii(s))
        self.assertTrue(len(s) > 0)


class TestRecordRecall(unittest.TestCase):
    def test_roundtrip(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            msgs = [{"role": "user", "content": "deploy checklist review"}]
            rid = record_episode(
                path, 7, "s1", msgs, "shipped ok", 2, 3, True
            )
            self.assertEqual(rid, 7)
            hits = episodic_recall(path, "deploy")
            self.assertEqual(len(hits), 1)
            self.assertIn("[turn #7]", hits[0])
            # case-insensitive
            hits2 = episodic_recall(path, "DEPLOY")
            self.assertEqual(len(hits2), 1)
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass

    def test_recall_limit(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            for i in range(1, 6):
                record_episode(
                    path, i, "s",
                    [{"role": "user", "content": "common topic run"}],
                    "final %d" % i, 1, 1, True,
                )
            hits = episodic_recall(path, "common", limit=2)
            self.assertEqual(len(hits), 2)
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass

    def test_no_match_and_empty_query(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            record_episode(
                path, 1, "s",
                [{"role": "user", "content": "alpha beta"}],
                "done", 0, 0, True,
            )
            self.assertEqual(episodic_recall(path, "zzz-nope"), [])
            self.assertEqual(episodic_recall(path, ""), [])
            self.assertEqual(episodic_recall(path, "   "), [])
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass

    def test_bad_ledger_id_returns_none(self):
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        try:
            self.assertIsNone(
                record_episode(path, "bad", "s", [], "x", 0, 0, False)
            )
        finally:
            try:
                os.unlink(path)
            except Exception:
                pass


if __name__ == "__main__":
    unittest.main()
