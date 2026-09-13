"""Tests for agent.pou_conduct (pure posture block)."""

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.pou_conduct import (
    conduct_posture_block,
    posture_for,
    should_clarify_first,
)


class TestPostureMapping(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(posture_for(0, None), "junior")
        self.assertEqual(posture_for(1, None), "junior")
        self.assertEqual(posture_for(2, None), "associate")
        self.assertEqual(posture_for(3, None), "senior")
        self.assertEqual(posture_for(10, None), "senior")
        self.assertEqual(posture_for(-5, None), "junior")

    def test_cautious_override(self):
        self.assertEqual(posture_for(1, 0.79), "junior+cautious")
        self.assertEqual(posture_for(2, 0.50), "associate+cautious")
        self.assertEqual(posture_for(3, 0.10), "senior+cautious")
        self.assertEqual(posture_for(2, 0.80), "associate")
        self.assertEqual(posture_for(3, 0.99), "senior")
        self.assertEqual(posture_for(1, None), "junior")


class TestClarifyMatrix(unittest.TestCase):
    def test_junior_always_clarifies(self):
        self.assertTrue(should_clarify_first(1, None, 0.0))
        self.assertTrue(should_clarify_first(1, 0.99, 0.1))

    def test_low_hci_clarifies(self):
        self.assertTrue(should_clarify_first(3, 0.70, 0.1))
        self.assertTrue(should_clarify_first(2, 0.79, 0.1))

    def test_complex_low_level_clarifies(self):
        self.assertTrue(should_clarify_first(2, 0.95, 0.7))
        self.assertTrue(should_clarify_first(2, 0.95, 0.9))

    def test_senior_routine_no_clarify(self):
        self.assertFalse(should_clarify_first(3, 0.95, 0.2))
        self.assertFalse(should_clarify_first(5, None, 0.69))


class TestPostureBlock(unittest.TestCase):
    def test_length_cap_and_ascii(self):
        for lvl in (1, 2, 3):
            for hci in (None, 0.5, 0.95):
                for corr in (0, 3):
                    block = conduct_posture_block(lvl, hci, corr)
                    self.assertLessEqual(len(block), 600)
                    block.encode("ascii")

    def test_includes_posture_and_rule(self):
        block = conduct_posture_block(2, 0.95, 0)
        self.assertIn("associate", block)
        self.assertIn("Execute routine tasks directly", block)

    def test_corrections_sentence(self):
        block = conduct_posture_block(2, 0.95, 2)
        self.assertIn("2", block)
        self.assertIn("correction", block.lower())
        plain = conduct_posture_block(2, 0.95, 0)
        self.assertNotIn("correction", plain.lower())

    def test_no_weakening_language(self):
        for lvl in (1, 2, 3):
            block = conduct_posture_block(lvl, 0.5, 1).lower()
            self.assertNotIn("bypass", block)
            self.assertNotIn("skip approval", block)
            self.assertNotIn("ignore denial", block)


if __name__ == "__main__":
    unittest.main()
