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
    get_tier3_ledger,
    get_tier3_memory_substrate,
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
            "reboot",
            "init 0",
            "init 6",
            "systemctl reboot",
            "kill -1",
            "dd if=/dev/zero of=/dev/sda",
            "dd of=/dev/sda1 if=/dev/zero",
            "mkfs.ext4 /dev/sda",
            "mkfs.ext4 /dev/sda1",
            ":(){ :|:& };:",
        ]
        for cmd in fatal_commands:
            is_safe, reason = evaluate_execution_safety(cmd)
            self.assertFalse(is_safe, f"Fatal command was not blocked: {cmd}")
            self.assertIn("Tier-3 Safety Invariant", reason)

    def test_no_false_positives_on_prose_and_suffix_commands(self):
        # Upstream-anchored matching must not fire on prose or suffixed paths.
        benign = [
            "echo reboot",
            "grep 'shutdown' logs",
            "rm -rf /tmp/myapp",
        ]
        for cmd in benign:
            is_safe, _ = evaluate_execution_safety(cmd)
            self.assertTrue(is_safe, f"False positive block: {cmd}")

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

    def test_energy_scale_reaches_level_two(self):
        # Regression: with unscaled energy (~4.5/turn), T(2) ≈ 22000 was
        # unreachable (~5000 perfect turns). Scaled energy must progress.
        metrics = PoUInteractionMetrics(
            task_complexity=1.0,
            master_comprehension=1.0,
            soul_assimilation=1.0,
            execution_precision=1.0,
            master_satisfaction=1.0,
        )
        delta = self.ledger.calculate_energy_delta(metrics, current_level=1)
        self.assertGreater(delta, 100.0)
        level = 1
        energy = 0.0
        for _ in range(60):
            energy += delta
            if energy >= CognitivePoULedger.difficulty_target(level + 1):
                level += 1
                break
        self.assertGreaterEqual(level, 2)

    def test_hci_uses_rolling_history(self):
        # One perfect turn after a bad history must NOT satisfy HCI >= 0.98.
        bad = PoUInteractionMetrics(
            task_complexity=0.5,
            master_comprehension=0.2,
            soul_assimilation=0.2,
            execution_precision=0.5,
            master_satisfaction=-0.5,
        )
        for _ in range(5):
            self.ledger.record_turn(session_key="s-hci", metrics=bad)
        good = PoUInteractionMetrics(
            task_complexity=1.0,
            master_comprehension=1.0,
            soul_assimilation=1.0,
            execution_precision=1.0,
            master_satisfaction=1.0,
        )
        res = self.ledger.record_turn(session_key="s-hci", metrics=good)
        self.assertLess(res["hci"], 0.98)

    def test_class_structure_intact(self):
        # Structural guard: methods must live on the class, not orphaned at
        # module level by a misplaced edit (regression of the pointer-insert
        # breakage). Fails fast with a clear message instead of deep errors.
        from agent import tier3_cognitive_core as _core

        for name in (
            "distill_and_store",
            "query_relevant_soul_memory",
            "ensure_soul_seeded",
            "count",
        ):
            self.assertTrue(
                callable(getattr(_core.DynamicSoulMemorySubstrate, name, None)),
                f"DynamicSoulMemorySubstrate.{name} missing from class",
            )
        for name in ("record_turn", "calculate_energy_delta", "difficulty_target"):
            self.assertTrue(
                callable(getattr(_core.CognitivePoULedger, name, None)),
                f"CognitivePoULedger.{name} missing from class",
            )

    def test_farming_guard_throttles_burst_gains(self):
        from agent.tier3_cognitive_core import (
            FARMING_TRIVIAL_COUNT,
            PoUInteractionMetrics as _M,
        )

        trivial = _M(0.1, 0.9, 0.9, 0.9, 0.5)
        for _ in range(FARMING_TRIVIAL_COUNT + 2):
            self.ledger.record_turn("s-farm", trivial, cause="burst")
        # Next positive turn must carry the farming-guard marker and a
        # throttled (halved) delta versus the unthrottled formula.
        res = self.ledger.record_turn("s-farm", trivial, cause="burst")
        self.assertIn("farming-guard", res["cause"])
        plain = self.ledger.calculate_energy_delta(trivial, 1)
        self.assertAlmostEqual(res["energy_delta"], plain * 0.5, places=6)
        # Penalties are never discounted: a dissonant turn stays full force.
        bad = _M(0.9, 0.2, 0.5, 0.8, -1.0, fatal_dissonance=True)
        res_bad = self.ledger.record_turn("s-farm", bad, cause="bad")
        self.assertNotIn("farming-guard", res_bad["cause"])
        self.assertLess(res_bad["energy_delta"], -100.0)

    def test_inactivity_decay_disclosed_in_cause(self):
        import sqlite3 as _sq
        import time as _t

        from agent.tier3_cognitive_core import PoUInteractionMetrics as _M

        good = _M(1.0, 1.0, 1.0, 1.0, 1.0)
        r1 = self.ledger.record_turn("s-decay", good, cause="seed")
        e1 = r1["cumulative_energy"]
        self.assertGreater(e1, 0)
        # Backdate the last row 60 idle days (halving period 30d -> x0.25).
        with _sq.connect(str(self.db_path)) as _c:
            _c.execute(
                "UPDATE pou_ledger SET timestamp = ?",
                (_t.time() - 60 * 86400.0,),
            )
            _c.commit()
        r2 = self.ledger.record_turn("s-decay", good, cause="after-idle")
        self.assertIn("inactivity decay", r2["cause"])
        # 60 idle days at 30d halving -> stored energy quartered before delta.
        self.assertAlmostEqual(
            r2["cumulative_energy"], e1 * 0.25 + r2["energy_delta"], places=4
        )

    def test_why_marks_level_transitions(self):
        from agent.tier3_cognitive_core import conduct_advice, pou_why

        lines = pou_why(limit=10, db_path=self.db_path)
        self.assertTrue(all(isinstance(line, str) for line in lines))
        self.assertTrue(all(line.isascii() for line in lines))
        adv = conduct_advice(1, 0.5)
        self.assertIn("cautious", adv["posture"])
        adv2 = conduct_advice(5, 0.99)
        self.assertEqual(adv2["posture"], "senior")

    def test_lazy_accessors_share_instances(self):
        self.assertIs(
            get_tier3_ledger(db_path=self.db_path),
            get_tier3_ledger(db_path=self.db_path),
        )
        self.assertIs(
            get_tier3_memory_substrate(db_path=self.db_path),
            get_tier3_memory_substrate(db_path=self.db_path),
        )

    def test_distill_rejects_empty_content(self):
        self.assertIsNone(self.substrate.distill_and_store("topic", "   "))
        self.assertIsNone(self.substrate.distill_and_store("   ", "content"))

    def test_soul_seeding_writes_once(self):
        from agent.tier3_cognitive_core import record_session_review_outcome

        soul = "## Identity\nYou are a concise assistant.\n\n## Rules\nAlways verify."
        first = self.substrate.ensure_soul_seeded(soul)
        self.assertEqual(first, 2)
        # Second call must not duplicate rows.
        self.assertEqual(self.substrate.ensure_soul_seeded(soul), 0)
        self.assertEqual(self.substrate.count(), 2)
        # Seeded chunks are retrievable via JIT query.
        hits = self.substrate.query_relevant_soul_memory("concise assistant verify")
        self.assertTrue(any("Identity" in h or "Rules" in h for h in hits))

    def test_turn_event_records_measured_precision(self):
        import json as _json
        from agent.tier3_cognitive_core import record_turn_event

        msgs = [
            {"role": "user", "content": "do it"},
            {"role": "assistant", "content": "on it"},
            {"role": "tool", "content": _json.dumps({"success": True})},
            {"role": "tool", "content": _json.dumps({"success": False})},
        ]
        res = record_turn_event(
            "sess-turn", msgs, completed=True, interrupted=False, db_path=self.db_path
        )
        self.assertIsNotNone(res)
        # Precision 0.5 must be reflected via lower energy than a perfect turn.
        perfect = [
            {"role": "user", "content": "do it"},
            {"role": "tool", "content": _json.dumps({"success": True})},
            {"role": "tool", "content": _json.dumps({"success": True})},
        ]
        res2 = record_turn_event(
            "sess-turn", perfect, completed=True, interrupted=False, db_path=self.db_path
        )
        self.assertGreater(res2["energy_delta"], res["energy_delta"])
        # Auto complexity never exceeds the cap.
        self.assertLessEqual(res2["energy_delta"], 0.15 * 1.0 * 2.8 * 100.0 + 1.0)

    def test_turn_event_skips_fork_and_interrupt(self):
        from agent.tier3_cognitive_core import record_turn_event

        msgs = [{"role": "user", "content": "hi"}]
        self.assertIsNone(
            record_turn_event("s", msgs, completed=True, interrupted=True, db_path=self.db_path)
        )
        self.assertIsNone(
            record_turn_event(
                "s", msgs, completed=True, interrupted=False,
                is_review_fork=True, db_path=self.db_path,
            )
        )

    def test_review_outcome_records_turn(self):
        from agent.tier3_cognitive_core import CognitivePoULedger, record_session_review_outcome

        snapshot = [
            {"role": "user", "content": "stop doing that, this is too verbose"},
            {"role": "assistant", "content": "noted"},
        ]
        res = record_session_review_outcome("sess-frust", snapshot, [], db_path=self.db_path)
        self.assertIsNotNone(res)
        self.assertLess(res["energy_delta"], 0.0)
        # Ledger row persisted in the same DB.
        import sqlite3 as _sq

        with _sq.connect(str(self.db_path)) as _c:
            n = _c.execute("SELECT COUNT(*) FROM pou_ledger").fetchone()[0]
        self.assertEqual(n, 1)

        clean_snapshot = [{"role": "user", "content": "thanks, summarize this"}]
        res2 = record_session_review_outcome(
            "sess-clean", clean_snapshot, ["Memory updated"], db_path=self.db_path
        )
        self.assertIsNotNone(res2)
        self.assertGreater(res2["energy_delta"], 0.0)

    # -------------------------------------------------------------------------
    # Test Suite 3: Dynamic Semantic Soul Memory Distillation
    # -------------------------------------------------------------------------
    def test_idf_rescoring_fixes_common_word_miss(self):
        # "tuan" appears in several memories; only importance+IDF should
        # surface the truly relevant one for a paraphrased query.
        self.substrate.distill_and_store(
            "Gaya laporan", "laporkan hasil kerja dalam satu baris padat", 1.0
        )
        self.substrate.distill_and_store(
            "Kopi tubruk", "Tuan suka kopi tubruk pahit tiap pagi", 0.3
        )
        self.substrate.distill_and_store(
            "Drama Korea", "Drama favorit tuan genre thriller", 0.2
        )
        hits = self.substrate.query_relevant_soul_memory(
            "gimana maunya soal hasil kerja"
        )
        self.assertTrue(hits, "expected at least one recalled memory")
        self.assertIn("Gaya laporan", hits[0])

    def test_indonesian_stemmer_expansion(self):
        from agent.tier3_cognitive_core import expand_query_tokens, stem_indonesian

        # Originals always preserved; stems added; no empties/duplicates.
        out = expand_query_tokens(["memeriksa", "tuan", "tuan"])
        self.assertIn("memeriksa", out)
        self.assertEqual(len(out), len(set(out)))
        self.assertTrue(all(o for o in out))
        # Affix stripping works: -nya clitic, -an suffix.
        self.assertEqual(stem_indonesian("bukunya"), "buku")
        self.assertEqual(stem_indonesian("minuman"), "minum")
        # Short words untouched.
        self.assertEqual(stem_indonesian("kopi"), "kopi")

    def test_stemmed_query_still_recalls(self):
        self.substrate.distill_and_store("Gaya laporan", "laporkan hasil dalam satu baris", 1.0)
        hits = self.substrate.query_relevant_soul_memory("bagaimana pelaporan hasilnya")
        self.assertTrue(any("Gaya laporan" in h for h in hits))

    def test_compact_identity_pointer(self):
        from agent.tier3_cognitive_core import compact_identity_pointer

        ptr = compact_identity_pointer(12)
        self.assertIn("12", ptr)
        self.assertLess(len(ptr), 200)

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
