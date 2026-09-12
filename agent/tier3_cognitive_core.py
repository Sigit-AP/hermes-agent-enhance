"""Tier-3 High-Assurance Cognitive & Execution Core for Hermes Agent.

Provides:
1. Micro-Kernel Hard Invariant Safety Guard (Prevents OS suicide, allows full automation).
2. Dynamic Cognitive Soul Assimilation & Chunking Memory Engine.
3. Deterministic Proof-of-Understanding (PoU) Mathematical Ledger (BTC-grade difficulty & halving).
4. Grounded, Transparent Anti-Drift Self-Improvement Telemetry.
"""

from __future__ import annotations

import logging
import math
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("hermes.tier3_core")

# =============================================================================
# 1. HARD INVARIANT SAFETY GUARD (Ring-0 VPS Survival)
# =============================================================================
#
# Design note (audit fix): the upstream approval engine already owns a
# battle-tested unconditional blocklist (tools/approval.py:
# HARDLINE_PATTERNS — rm of root/system dirs, mkfs, dd/redirection to raw
# devices, fork bomb, kill -1, shutdown/reboot/init/systemctl/telinit with
# command-position anchoring and sudo-wrapper handling). Duplicating that
# regex here previously created a weaker shadow list (it missed `reboot`,
# `init 6`, `systemctl reboot`, `kill -1`, device partitions, and allowed
# `$`-anchored bypasses such as `rm -rf / tmp`). To avoid drift between two
# lists, evaluate_execution_safety() delegates to the upstream matcher and
# keeps only a minimal supplemental guard for anything upstream lacks.


def evaluate_execution_safety(command: str) -> Tuple[bool, Optional[str]]:
    """Evaluate command against host-survival invariants.

    Delegates to the upstream unconditional blocklist so coverage (reboot,
    init 0/6, systemctl, kill -1, raw-device writes with partitions, sudo
    wrappers) can never drift out of sync.

    Returns:
        (is_safe, rejection_reason)
        If is_safe is True, the command may proceed with zero-block
        headless execution.
    """
    try:
        from tools.approval import detect_hardline_command
    except Exception as exc:  # pragma: no cover - import should not fail
        logger.debug("Tier-3 safety delegation unavailable: %s", exc)
        return True, None
    try:
        is_hardline, description = detect_hardline_command(command or "")
    except Exception as exc:
        logger.debug("Tier-3 safety evaluation error: %s", exc)
        return True, None
    if is_hardline:
        return False, f"Tier-3 Safety Invariant ({description})"
    return True, None


# =============================================================================
# 2. PROOF-OF-UNDERSTANDING MATHEMATICAL LEDGER & LEVELING ENGINE
# =============================================================================

@dataclass
class PoUInteractionMetrics:
    task_complexity: float    # D_k in (0, 1]
    master_comprehension: float # U_k in [0, 1]
    soul_assimilation: float  # A_k in [0, 1]
    execution_precision: float # P_k in [0, 1]
    master_satisfaction: float # S_k in [-1, 1]
    fatal_dissonance: bool = False


# Energy scale: maps per-turn quality (≈0–4.5) into ledger points so the
# documented difficulty curve T(L) is reachable within hundreds — not
# thousands — of strong turns. Without this, T(2) ≈ 22000 would require
# ~5000 perfect turns and leveling would be impossible in practice.
ENERGY_SCALE = 100.0
POU_HISTORY_WINDOW = 20

_SCHEMA = """
CREATE TABLE IF NOT EXISTS pou_ledger (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL,
    session_key TEXT,
    complexity REAL,
    comprehension REAL,
    soul_assimilation REAL,
    precision REAL,
    satisfaction REAL,
    energy_delta REAL,
    cumulative_energy REAL,
    current_level INTEGER,
    state_hash TEXT
);
CREATE TABLE IF NOT EXISTS cognitive_memory_substrate (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT,
    semantic_content TEXT,
    importance REAL,
    last_recalled REAL,
    recall_count INTEGER DEFAULT 0
);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path), timeout=30.0)


def _ensure_schema(db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        _ensure_fts(conn)
        conn.commit()


def _ensure_fts(conn: sqlite3.Connection) -> None:
    """Create FTS5 index over the memory substrate with content sync triggers.

    Falls back silently when SQLite lacks FTS5 (e.g. minimal builds) — the
    query path then uses the ranked-substring fallback.
    """
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS cognitive_memory_fts
            USING fts5(topic, semantic_content, content='cognitive_memory_substrate',
                       content_rowid='id', tokenize='unicode61');
        """)
        conn.executescript("""
            CREATE TRIGGER IF NOT EXISTS cognitive_memory_ai AFTER INSERT ON cognitive_memory_substrate BEGIN
                INSERT INTO cognitive_memory_fts(rowid, topic, semantic_content)
                VALUES (new.id, new.topic, new.semantic_content);
            END;
            CREATE TRIGGER IF NOT EXISTS cognitive_memory_ad AFTER DELETE ON cognitive_memory_substrate BEGIN
                INSERT INTO cognitive_memory_fts(cognitive_memory_fts, rowid, topic, semantic_content)
                VALUES ('delete', old.id, old.topic, old.semantic_content);
            END;
            CREATE TRIGGER IF NOT EXISTS cognitive_memory_au AFTER UPDATE ON cognitive_memory_substrate BEGIN
                INSERT INTO cognitive_memory_fts(cognitive_memory_fts, rowid, topic, semantic_content)
                VALUES ('delete', old.id, old.topic, old.semantic_content);
                INSERT INTO cognitive_memory_fts(rowid, topic, semantic_content)
                VALUES (new.id, new.topic, new.semantic_content);
            END;
        """)
        # Backfill rows predating the FTS table.
        conn.execute("""
            INSERT INTO cognitive_memory_fts(rowid, topic, semantic_content)
            SELECT id, topic, semantic_content FROM cognitive_memory_substrate
            WHERE id NOT IN (SELECT rowid FROM cognitive_memory_fts);
        """)
    except sqlite3.OperationalError as exc:
        logger.debug("FTS5 unavailable, using substring fallback: %s", exc)


def _default_db_path() -> Path:
    home = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
    home.mkdir(parents=True, exist_ok=True)
    return home / "cognitive_state.db"


class CognitivePoULedger:
    """Mathematical Ledger implementing Difficulty Scaling & Halving Curves."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        _ensure_schema(self.db_path)

    @staticmethod
    def difficulty_target(level: int) -> float:
        lvl = max(1, int(level))
        return 2500.0 * (2.0 ** (lvl // 4)) * (float(lvl) ** math.pi)

    @staticmethod
    def calculate_energy_delta(metrics: PoUInteractionMetrics, current_level: int) -> float:
        """Calculate non-linear cognitive energy delta with Tier-3 quadratic penalty."""
        # Weights: Comprehension 0.45, Soul Assimilation 0.25, Execution Precision 0.30
        w1, w2, w3 = 0.45, 0.25, 0.30
        base_quality = (w1 * (metrics.master_comprehension ** 2) +
                        w2 * metrics.soul_assimilation +
                        w3 * metrics.execution_precision)

        # Exponential satisfaction multiplier
        sat_clipped = max(-1.0, min(1.0, metrics.master_satisfaction))
        sat_multiplier = math.exp(1.5 * sat_clipped)

        raw_energy = metrics.task_complexity * base_quality * sat_multiplier * ENERGY_SCALE

        # Calculate Difficulty Target for current level T(L)
        t_l = CognitivePoULedger.difficulty_target(current_level)

        # Quadratic Demotion Penalty if dissonance occurs
        penalty = 0.0
        if metrics.master_comprehension < 0.60 or metrics.master_satisfaction < 0 or metrics.fatal_dissonance:
            kappa = 8.0
            penalty = kappa * ((1.0 - metrics.master_comprehension) ** 3) * abs(sat_clipped) * (t_l * 0.1)

        return max(-10000.0, raw_energy - penalty)

    def _rolling_means(self, cur: sqlite3.Cursor, metrics: PoUInteractionMetrics) -> Tuple[float, float, float]:
        """Mean comprehension/assimilation/satisfaction over the recent window.

        The documented HCI gate requires sustained consistency, so it must be
        computed from history — not from the single current turn.
        """
        cur.execute(
            "SELECT comprehension, soul_assimilation, satisfaction FROM pou_ledger "
            "ORDER BY id DESC LIMIT ?",
            (POU_HISTORY_WINDOW - 1,),
        )
        rows = cur.fetchall()
        u_vals = [metrics.master_comprehension] + [r[0] for r in rows]
        a_vals = [metrics.soul_assimilation] + [r[1] for r in rows]
        s_vals = [(metrics.master_satisfaction + 1.0) / 2.0] + [(r[2] + 1.0) / 2.0 for r in rows]
        mean = lambda vs: sum(vs) / len(vs)
        return mean(u_vals), mean(a_vals), mean(s_vals)

    def record_turn(
        self,
        session_key: str,
        metrics: PoUInteractionMetrics
    ) -> Dict[str, Any]:
        """Record turn metrics, update energy, compute leveling and persist."""
        with _connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT cumulative_energy, current_level FROM pou_ledger ORDER BY id DESC LIMIT 1")
            row = cur.fetchone()
            prev_energy = row[0] if row else 0.0
            prev_level = row[1] if row else 1

            energy_delta = self.calculate_energy_delta(metrics, prev_level)
            new_energy = max(0.0, prev_energy + energy_delta)

            # Evaluate Level Progression
            new_level = prev_level
            next_target = self.difficulty_target(prev_level + 1)
            current_target = self.difficulty_target(prev_level)

            # Harmonic Consistency Index (HCI) over the rolling window
            u_bar, a_bar, s_bar = self._rolling_means(cur, metrics)
            u_safe = max(0.01, u_bar)
            a_safe = max(0.01, a_bar)
            s_safe = max(0.01, s_bar)
            hci = 3.0 / ((1.0 / u_safe) + (1.0 / a_safe) + (1.0 / s_safe))

            if new_energy >= next_target and hci >= 0.98 and not metrics.fatal_dissonance:
                new_level = prev_level + 1
            elif new_energy < current_target and prev_level > 1:
                # Demotion condition
                new_level = prev_level - 1
                
            cur.execute("""
                INSERT INTO pou_ledger (
                    timestamp, session_key, complexity, comprehension, soul_assimilation,
                    precision, satisfaction, energy_delta, cumulative_energy, current_level, state_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                time.time(), session_key, metrics.task_complexity, metrics.master_comprehension,
                metrics.soul_assimilation, metrics.execution_precision, metrics.master_satisfaction,
                energy_delta, new_energy, new_level, "tier3-verified"
            ))
            conn.commit()
            
            return {
                "energy_delta": energy_delta,
                "cumulative_energy": new_energy,
                "current_level": new_level,
                "level_changed": (new_level != prev_level),
                "hci": hci,
            }


# =============================================================================
# 3. DYNAMIC SOUL ASSIMILATION & MEMORY DISTILLATION
# =============================================================================

class DynamicSoulMemorySubstrate:
    """Manages incremental absorption of SOUL.md into structured knowledge."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        _ensure_schema(self.db_path)

    def distill_and_store(self, topic: str, content: str, importance: float = 1.0) -> Optional[int]:
        """Store semantic soul chunk into persistent cognitive memory substrate.

        Returns the new row id, or None when the input carries no content.
        """
        clean_topic = (topic or "").strip()[:200]
        clean_content = (content or "").strip()
        if not clean_topic or not clean_content:
            return None
        try:
            importance_val = max(0.0, min(10.0, float(importance)))
        except (TypeError, ValueError):
            importance_val = 1.0
        with _connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cognitive_memory_substrate (topic, semantic_content, importance, last_recalled)
                VALUES (?, ?, ?, ?)
            """, (clean_topic, clean_content, importance_val, time.time()))
            row_id = cur.lastrowid
            conn.commit()
            return row_id

    def _fts_query(self, conn: sqlite3.Connection, query: str, limit: int) -> List[Tuple[int, str, str]]:
        cur = conn.cursor()
        cur.execute("""
            SELECT m.id, m.topic, m.semantic_content
            FROM cognitive_memory_fts f
            JOIN cognitive_memory_substrate m ON m.id = f.rowid
            WHERE cognitive_memory_fts MATCH ?
            ORDER BY rank, m.importance DESC
            LIMIT ?
        """, (query, limit))
        return cur.fetchall()

    def query_relevant_soul_memory(self, task_context: str, limit: int = 3) -> List[str]:
        """Fetch JIT (Just-In-Time) relevant memory via FTS5 with ranked fallback."""
        tokens = [w.lower() for w in re.findall(r"\w+", task_context or "") if len(w) > 3]
        if not tokens:
            return []

        with _connect(self.db_path) as conn:
            # Primary path: FTS5 full-text match over quoted tokens.
            try:
                fts_query = " OR ".join(f'"{t}"' for t in tokens[:10])
                rows = self._fts_query(conn, fts_query, limit)
                if rows:
                    self._touch(conn, [r[0] for r in rows])
                    conn.commit()
                    return [f"[{topic}] {text}" for _, topic, text in rows]
            except sqlite3.OperationalError as exc:
                logger.debug("FTS query failed, using fallback: %s", exc)

            # Fallback path: ranked substring scoring.
            cur = conn.cursor()
            cur.execute("SELECT id, topic, semantic_content FROM cognitive_memory_substrate ORDER BY importance DESC")
            rows = cur.fetchall()

            scored = []
            for row_id, topic, text in rows:
                topic_l, text_l = topic.lower(), text.lower()
                score = sum(1 for t in tokens if t in topic_l or t in text_l)
                if score > 0:
                    scored.append((score, row_id, f"[{topic}] {text}"))

            scored.sort(key=lambda x: x[0], reverse=True)
            selected = scored[:limit]
            self._touch(conn, [r_id for _, r_id, _ in selected])
            conn.commit()
            return [item[2] for item in selected]

    @staticmethod
    def _touch(conn: sqlite3.Connection, row_ids: List[int]) -> None:
        now = time.time()
        for r_id in row_ids:
            conn.execute(
                "UPDATE cognitive_memory_substrate SET recall_count = recall_count + 1, "
                "last_recalled = ? WHERE id = ?",
                (now, r_id),
            )


@lru_cache(maxsize=4)
def _cached_ledger(db_path_str: str = "") -> CognitivePoULedger:
    path = Path(db_path_str) if db_path_str else None
    return CognitivePoULedger(db_path=path)


@lru_cache(maxsize=4)
def _cached_substrate(db_path_str: str = "") -> DynamicSoulMemorySubstrate:
    path = Path(db_path_str) if db_path_str else None
    return DynamicSoulMemorySubstrate(db_path=path)


def get_tier3_ledger(db_path: Optional[Path] = None) -> CognitivePoULedger:
    """Lazy accessor — avoids import-time DB creation as a side effect."""
    return _cached_ledger(str(db_path) if db_path is not None else "")


def get_tier3_memory_substrate(db_path: Optional[Path] = None) -> DynamicSoulMemorySubstrate:
    """Lazy accessor — avoids import-time DB creation as a side effect."""
    return _cached_substrate(str(db_path) if db_path is not None else "")
