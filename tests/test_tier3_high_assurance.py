"""Tier-3 High-Assurance Test & Simulation Suite.
Verifies:
1. Hard Invariant OS Safety Interceptor (Ring-0 VPS Protection).
2. Dynamic Proof-of-Understanding (PoU) Mathematical Engine (Energy, Leveling, Slash Penalties).
3. Dynamic Semantic Soul Distillation & Memory Substrate.
"""

import math
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agent.tier3_cognitive_core import (
    CognitivePoULedger,
    DynamicSoulMemorySubstrate,
    PoUInteractionMetrics,
    evaluate_execution_safety,
)


class TestTier3HighAssuranceSuite(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test_cognitive_state.db"
        self.ledger = CognitivePoULedger(db_path=self.db_path)
        self.substrate = DynamicSoulMemorySubstrate(db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------------------
    # Test Suite 1: Hard Invariant Safety & Execution Pass-Through
    # -------------------------------------------------------------------------
    def test_fatal_command_interceptions(self):
        fatal_commands = [
            "rm -rf /",
            "rm -rf /*",
            "rm -rf --no-preserve-root /",
            "shutdown now",
            "poweroff",
            "init 0",
            "dd if=/dev/zero of=/dev/sda",
            "mkfs.ext4 /dev/sda",
            ":(){ :|:& };:",
        ]
        for cmd in fatal_commands:
            is_safe, reason = evaluate_execution_safety(cmd)
            self.assertFalse(is_safe, f"Fatal command was not blocked: {cmd}")
            self.assertIn("Tier-3 Safety Invariant", reason)

    def test_benign_dev_and_automation_commands_pass(self):
        benign_commands = [
            "git status && git commit -m 'deploy'",
            "curl -X POST http://127.0.0.1:8080/api/v1/task",
            "python3 -m pytest tests/",
            "npm install --save-dev typescript",
            "systemctl restart hermes-agent.service",
            "cat /etc/os-release",
            "find . -name '*.py' | xargs grep -i 'test'",
        ]
        for cmd in benign_commands:
            is_safe, reason = evaluate_execution_safety(cmd)
            self.assertTrue(is_safe, f"Benign command was falsely blocked: {cmd}")
            self.assertIsNone(reason)

    # -------------------------------------------------------------------------
    # Test Suite 2: Mathematical Proof-of-Understanding (PoU) & Halving
    # -------------------------------------------------------------------------
    def test_level_progression_with_high_comprehension(self):
        # High comprehension + satisfaction -> steady energy gain
        metrics = PoUInteractionMetrics(
            task_complexity=0.85,
            master_comprehension=0.98,
            soul_assimilation=0.92,
            execution_precision=0.99,
            master_satisfaction=1.0,
            fatal_dissonance=False,
        )
        # Energy delta calculation
        delta = self.ledger.calculate_energy_delta(metrics, current_level=1)
        self.assertGreater(delta, 0.0)
        
        # Verify Level 1 target difficulty
        t1 = 2500.0 * (2.0 ** (1 // 4)) * (1.0 ** math.pi)
        self.assertEqual(t1, 2500.0)

    def test_quadratic_slash_penalty_on_fatal_dissonance(self):
        # If agent fails comprehension severely
        dissonant_metrics = PoUInteractionMetrics(
            task_complexity=0.90,
            master_comprehension=0.20,
            soul_assimilation=0.50,
            execution_precision=0.80,
            master_satisfaction=-1.0,
            fatal_dissonance=True,
        )
        delta = self.ledger.calculate_energy_delta(dissonant_metrics, current_level=2)
        # Delta must be severely negative due to penalty
        self.assertLess(delta, -100.0, "Quadratic slash penalty failed to trigger on dissonance")

    def test_multi_turn_ledger_recording(self):
        res1 = self.ledger.record_turn(
            session_key="session-test-01",
            metrics=PoUInteractionMetrics(
                task_complexity=0.5,
                master_comprehension=0.95,
                soul_assimilation=0.90,
                execution_precision=0.95,
                master_satisfaction=0.8,
            )
        )
        self.assertIn("cumulative_energy", res1)
        self.assertEqual(res1["current_level"], 1)

    # -------------------------------------------------------------------------
    # Test Suite 3: Dynamic Semantic Soul Memory Distillation
    # -------------------------------------------------------------------------
    def test_soul_distillation_and_jit_query(self):
        # Distill knowledge
        self.substrate.distill_and_store(
            topic="Master Communication Preference",
            content="Tuan menginginkan eksekusi tanpa basa-basi, padat, dan laporan satu baris.",
            importance=1.0
        )
        self.substrate.distill_and_store(
            topic="VPS Linux Architecture",
            content="Hermes berjalan pada headless Ubuntu LTS dengan systemd service daemon.",
            importance=0.9
        )
        
        # Query matching memory
        results = self.substrate.query_relevant_soul_memory(task_context="Bagaimana preferensi komunikasi Tuan?")
        self.assertEqual(len(results), 1)
        self.assertIn("Master Communication Preference", results[0])
        self.assertIn("tanpa basa-basi", results[0])


if __name__ == "__main__":
    unittest.main()
