"""Integration: measure -> record -> why(+episodes) -> calibrate chain.

Proves the living loop is one connected system (ASCII-only throughout).
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.pou_calibration import calibration_report
from agent.pou_conduct import conduct_posture_block, should_clarify_first
from agent.pou_episodic import episodic_recall, get_episode, record_episode
from agent.pou_understanding import measure_turn_understanding
from agent.tier3_cognitive_core import (
    PoUInteractionMetrics,
    evaluate_execution_safety,
    get_tier3_ledger,
    pou_status,
    pou_why,
    pou_why_with_episodes,
)


def _metrics(comp=0.9, sat=0.5, prec=1.0, cx=0.5):
    return PoUInteractionMetrics(cx, comp, 0.7, prec, sat)


class TestLivingChain(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="living_"))
        self.db = self.tmp / "cog.db"
        self.ledger = get_tier3_ledger(db_path=self.db)

    def tearDown(self):
        import gc
        import shutil

        gc.collect()
        shutil.rmtree(str(self.tmp), ignore_errors=True)

    def test_measure_record_why_calibrate_chain(self):
        msgs = [
            {"role": "user", "content": "Deploy the app now"},
            {"role": "tool", "content": json.dumps({"success": True})},
        ]
        measured = measure_turn_understanding(msgs, True, False, final_response="deployed ok")
        res = self.ledger.record_turn(
            "chain",
            PoUInteractionMetrics(0.3, measured["comprehension"], 0.6,
                                 1.0, measured["satisfaction"]),
            cause="chain turn",
        )
        self.assertIn("row_id", res)
        ep = record_episode(self.db, res["row_id"], "chain", msgs, "deployed ok", 1, 1, True)
        self.assertEqual(ep, res["row_id"])
        self.assertIn("chain turn", pou_why(limit=5, db_path=self.db)[-1])
        lines = pou_why_with_episodes(limit=5, db_path=self.db)
        self.assertTrue(any("#turn" in line for line in lines))
        rep = calibration_report(self.db)
        self.assertEqual(rep["turns"], 1)
        st = pou_status(db_path=self.db)
        self.assertEqual(st["turns"], 1)
        block = conduct_posture_block(st["level"], st["hci"], 0)
        block.encode("ascii")
        for line in lines:
            line.encode("ascii")

    def test_gate_matrix_never_weakens_safety(self):
        hardline = ["reboot", "shutdown now", "poweroff", "init 0", "init 6",
                    "kill -1", "rm -rf /", "mkfs.ext4 /dev/sda",
                    "dd if=/dev/zero of=/dev/sda", ":(){ :|:& };:"]
        for cmd in hardline:
            safe, _ = evaluate_execution_safety(cmd)
            self.assertFalse(safe, cmd)
        # Conduct posture must never claim to bypass anything.
        block = conduct_posture_block(5, 0.99, 0).lower()
        for forbidden in ("bypass", "disable", "ignore approval", "skip approval", "yolo"):
            self.assertNotIn(forbidden, block)
        self.assertFalse(should_clarify_first(5, 0.99, 0.2))

    def test_episode_links_to_ledger_cause(self):
        res = self.ledger.record_turn("ep", _metrics(), cause="ep cause")
        record_episode(self.db, res["row_id"], "ep",
                       [{"role": "user", "content": "do thing"}],
                       "did thing", 0, 0, True)
        got = get_episode(self.db, res["row_id"])
        self.assertIsNotNone(got)
        self.assertIn("do thing", got)
        hits = episodic_recall(self.db, "do thing")
        self.assertTrue(any("turn #" in h for h in hits))
        self.assertTrue(all(h.isascii() for h in hits))


if __name__ == "__main__":
    unittest.main()
