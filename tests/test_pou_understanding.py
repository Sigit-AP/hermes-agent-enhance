"""Tests for agent.pou_understanding (pure, no I/O/DB). ASCII-only."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.pou_understanding import (
    CORRECTION_PHRASES,
    count_corrections,
    measure_turn_understanding,
    tool_retry_stats,
)


class TestCorrectionCounting(unittest.TestCase):
    def test_counts_each_text_once(self):
        texts = ["That's wrong, redo it", "looks good thanks"]
        self.assertEqual(count_corrections(texts), 1)

    def test_case_insensitive(self):
        self.assertEqual(count_corrections(["STOP DOING that"]), 1)

    def test_multiple_phrases_one_text_counts_once(self):
        self.assertEqual(
            count_corrections(["that's wrong, useless, not what i asked"]), 1
        )

    def test_empty_and_non_string(self):
        self.assertEqual(count_corrections([]), 0)
        self.assertEqual(count_corrections([None, 42, "fine"]), 0)

    def test_all_phrases_ascii(self):
        for phrase in CORRECTION_PHRASES:
            phrase.encode("ascii")


class TestRetryStats(unittest.TestCase):
    def test_success_false_json_is_error(self):
        msgs = [
            {"role": "user", "content": "go"},
            {"role": "tool", "content": '{"success": false}'},
            {"role": "tool", "content": '{"success": true}'},
        ]
        self.assertEqual(tool_retry_stats(msgs), (1, 2))

    def test_plain_text_error_regex(self):
        msgs = [
            {"role": "user", "content": "go"},
            {"role": "tool", "content": "Traceback: something failed"},
        ]
        self.assertEqual(tool_retry_stats(msgs), (1, 1))

    def test_non_json_counts_as_success(self):
        msgs = [
            {"role": "user", "content": "go"},
            {"role": "tool", "content": "all done, here is the file"},
        ]
        self.assertEqual(tool_retry_stats(msgs), (0, 1))

    def test_malformed_json_falls_back_to_text(self):
        msgs = [
            {"role": "user", "content": "go"},
            {"role": "tool", "content": '{"success": tru'},
        ]
        self.assertEqual(tool_retry_stats(msgs), (0, 1))
        msgs2 = [
            {"role": "user", "content": "go"},
            {"role": "tool", "content": '{"broken json with error inside'},
        ]
        self.assertEqual(tool_retry_stats(msgs2), (1, 1))

    def test_only_since_last_user_message(self):
        msgs = [
            {"role": "tool", "content": '{"success": false}'},
            {"role": "user", "content": "retry"},
            {"role": "tool", "content": "ok done"},
        ]
        self.assertEqual(tool_retry_stats(msgs), (0, 1))

    def test_empty(self):
        self.assertEqual(tool_retry_stats([]), (0, 0))


class TestMeasureTurn(unittest.TestCase):
    def test_clean_completed_turn(self):
        out = measure_turn_understanding(
            [{"role": "user", "content": "please help"}], True, False
        )
        self.assertEqual(out["comprehension"], 0.85)
        self.assertEqual(out["satisfaction"], 0.2)
        self.assertIsNone(out["precision_hint"])

    def test_correction_penalty_and_satisfaction(self):
        out = measure_turn_understanding(
            [{"role": "user", "content": "that's wrong, not what i asked"}],
            True,
            False,
        )
        self.assertAlmostEqual(out["comprehension"], 0.70)
        self.assertEqual(out["satisfaction"], -0.6)

    def test_interrupted_overrides_satisfaction(self):
        out = measure_turn_understanding(
            [{"role": "user", "content": "useless"}], True, True
        )
        self.assertEqual(out["satisfaction"], -0.3)
        self.assertAlmostEqual(out["comprehension"], 0.70)

    def test_precision_hint_from_tools(self):
        msgs = [
            {"role": "user", "content": "go"},
            {"role": "tool", "content": '{"success": false}'},
            {"role": "tool", "content": "ok"},
        ]
        out = measure_turn_understanding(msgs, True, False)
        self.assertAlmostEqual(out["precision_hint"], 0.5)

    def test_empty_messages(self):
        out = measure_turn_understanding([], False, False)
        self.assertEqual(out["comprehension"], 0.85)
        self.assertEqual(out["satisfaction"], 0.0)
        self.assertIsNone(out["precision_hint"])

    def test_unicode_safety(self):
        msgs = [{"role": "user", "content": "caf\u00e9 \u4e2d\u6587 \U0001f600 ok"}]
        out = measure_turn_understanding(msgs, True, False)
        self.assertEqual(out["comprehension"], 0.85)
        self.assertEqual(out["satisfaction"], 0.2)

    def test_floor(self):
        texts = ["useless"] * 20
        msgs = [{"role": "user", "content": t} for t in texts]
        out = measure_turn_understanding(msgs, False, False)
        self.assertEqual(out["comprehension"], 0.1)


if __name__ == "__main__":
    unittest.main()
