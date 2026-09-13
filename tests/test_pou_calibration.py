"""Tests for agent.pou_calibration.calibration_report (read-only).

Builds temp DBs via agent.tier3_cognitive_core.CognitivePoULedger;
direct SQL is used only to craft deterministic level/cause patterns
the live dynamics cannot produce (demotions can never exceed
promotions from level 1 since the floor is L1).
"""

import gc
import shutil
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.pou_calibration import calibration_report
from agent.tier3_cognitive_core import (
    ENERGY_SCALE,
    CognitivePoULedger,
    PoUInteractionMetrics,
)


def _good(complexity=0.8) -> PoUInteractionMetrics:
    return PoUInteractionMetrics(
        task_complexity=complexity,
        master_comprehension=0.95,
        soul_assimilation=0.9,
        execution_precision=1.0,
        master_satisfaction=0.8,
    )


def _bad() -> PoUInteractionMetrics:
    return PoUInteractionMetrics(
        task_complexity=0.7,
        master_comprehension=0.2,
        soul_assimilation=0.3,
        execution_precision=0.4,
        master_satisfaction=-1.0,
    )


def _weak() -> PoUInteractionMetrics:
    return PoUInteractionMetrics(
        task_complexity=0.03,
        master_comprehension=0.5,
        soul_assimilation=0.5,
        execution_precision=0.5,
        master_satisfaction=0.0,
    )


def _snapshot(db_path: Path):
    with sqlite3.connect(str(db_path), timeout=30.0) as conn:
        try:
            rows = conn.execute(
                "SELECT energy_delta, current_level, hci, cause, timestamp "
                "FROM pou_ledger ORDER BY id"
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        return rows


class TestPouCalibration(unittest.TestCase):
    def _new_db(self, name="cog.db"):
        # Repo convention (test_tier3_high_assurance): mkdtemp + rmtree
        # ignore_errors; gc.collect() first releases SQLite traceback
        # cycles that otherwise lock the file on Windows.
        tmp = tempfile.mkdtemp(prefix="pou_cal_")
        self.addCleanup(shutil.rmtree, tmp, True)
        self.addCleanup(gc.collect)
        return Path(tmp) / name

    def test_empty_db(self):
        db = self._new_db()
        CognitivePoULedger(db)
        rep = calibration_report(db)
        self.assertEqual(rep["turns"], 0)
        self.assertEqual(rep["recommendations"], [])

    def test_missing_table(self):
        db = self._new_db("bare.db")
        with sqlite3.connect(str(db), timeout=30.0) as conn:
            conn.execute("CREATE TABLE other (id INTEGER PRIMARY KEY)")
            conn.commit()
        rep = calibration_report(db)
        self.assertEqual(rep["turns"], 0)
        self.assertEqual(rep["recommendations"], [])

    def test_missing_file(self):
        db = self._new_db("nope.db")
        rep = calibration_report(db)
        self.assertEqual(rep["turns"], 0)
        self.assertEqual(rep["recommendations"], [])

    def test_small_db_collect_more_data(self):
        db = self._new_db()
        ledger = CognitivePoULedger(db)
        for i in range(5):
            ledger.record_turn(f"s{i}", _good(), cause=f"run {i}")
        before = _snapshot(db)
        rep = calibration_report(db)
        after = _snapshot(db)
        self.assertEqual(rep["turns"], 5)
        self.assertEqual(before, after)  # read-only: rows untouched
        recs = rep["recommendations"]
        self.assertIn("collect more data: 5/50 turns", recs)
        self.assertTrue(any(r.startswith("constants: ") for r in recs))
        for r in recs:
            r.encode("ascii")  # ASCII-only
        self.assertEqual(sum(rep["level_histogram"].values()), 5)
        self.assertGreaterEqual(rep["mean_hci"], 0.0)
        self.assertGreaterEqual(rep["days_span"], 0.0)

    def test_mean_nonpositive_rule(self):
        db = self._new_db()
        ledger = CognitivePoULedger(db)
        for i in range(25):
            ledger.record_turn(f"s{i}", _bad(), cause=f"bad {i}")
        rep = calibration_report(db)
        self.assertEqual(rep["turns"], 25)
        self.assertLessEqual(rep["mean_delta"], 0)
        self.assertIn(
            "energy mean non-positive: consider raising ENERGY_SCALE",
            rep["recommendations"],
        )

    def test_no_promotions_100_rule(self):
        db = self._new_db()
        ledger = CognitivePoULedger(db)
        for i in range(105):
            ledger.record_turn(f"s{i}", _weak(), cause=f"weak {i}")
        rep = calibration_report(db)
        self.assertGreaterEqual(rep["turns"], 100)
        self.assertEqual(rep["promotions"], 0)
        self.assertIn(
            "no promotions in 100+ turns: review T0/curve",
            rep["recommendations"],
        )

    def test_demotions_exceed_rule(self):
        db = self._new_db()
        CognitivePoULedger(db)  # ensures schema only
        with sqlite3.connect(str(db), timeout=30.0) as conn:
            for i in range(35):
                lvl = 2 if i == 0 else 1  # one demotion, zero promotions
                conn.execute(
                    "INSERT INTO pou_ledger (timestamp, session_key, complexity,"
                    " comprehension, soul_assimilation, precision, satisfaction,"
                    " energy_delta, cumulative_energy, current_level,"
                    " state_hash, cause, hci)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (1700000000.0 + i, f"s{i}", 0.5, 0.5, 0.5, 0.5, 0.0,
                     10.0, 100.0 + i, lvl, "tier3-verified",
                     f"craft {i}", 0.5),
                )
            conn.commit()
        rep = calibration_report(db)
        self.assertEqual(rep["turns"], 35)
        self.assertEqual(rep["promotions"], 0)
        self.assertEqual(rep["demotions"], 1)
        self.assertIn(
            "demotions exceed promotions: check penalty kappa",
            rep["recommendations"],
        )

    def test_cause_marker_counts(self):
        db = self._new_db()
        CognitivePoULedger(db)
        with sqlite3.connect(str(db), timeout=30.0) as conn:
            markers = [
                "run 0 | farming-guard x0.5 (30 trivial turns/h)",
                "run 1 | inactivity decay x0.50 (30.0d idle)",
                'run 2 | quest done: "Precision streak" +100E',
                "run 3 | farming-guard x0.5 (31 trivial turns/h)",
                "run 4",
            ]
            for i, cause in enumerate(markers):
                conn.execute(
                    "INSERT INTO pou_ledger (timestamp, session_key, complexity,"
                    " comprehension, soul_assimilation, precision, satisfaction,"
                    " energy_delta, cumulative_energy, current_level,"
                    " state_hash, cause, hci)"
                    " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (1700000000.0 + i * 10, f"s{i}", 0.5, 0.8, 0.8, 0.9,
                     0.5, 50.0, 100.0 + i * 50, 1, "tier3-verified",
                     cause, 0.8),
                )
            conn.commit()
        rep = calibration_report(db)
        self.assertEqual(rep["farming_hits"], 2)
        self.assertEqual(rep["decay_hits"], 1)
        self.assertEqual(rep["quest_hits"], 1)
        self.assertIn("farming guard active (2 hits): healthy",
                      rep["recommendations"])
        self.assertAlmostEqual(rep["days_span"], 40.0 / 86400.0, places=9)

    def test_read_only_and_constants_intact(self):
        db = self._new_db()
        ledger = CognitivePoULedger(db)
        for i in range(3):
            ledger.record_turn(f"s{i}", _good(), cause=f"run {i}")
        before = _snapshot(db)
        calibration_report(db)
        self.assertEqual(_snapshot(db), before)
        self.assertEqual(ENERGY_SCALE, 100.0)  # never mutated
        rep = calibration_report(db)
        self.assertIn("ENERGY_SCALE=100.0", rep["recommendations"][-1])


if __name__ == "__main__":
    unittest.main()
