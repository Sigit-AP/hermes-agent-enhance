"""Tier-3 High-Assurance Cognitive & Execution Core for Hermes Agent.

Provides:
1. Micro-Kernel Hard Invariant Safety Guard (Prevents OS suicide, allows full automation).
2. Dynamic Cognitive Soul Assimilation & Chunking Memory Engine.
3. Deterministic Proof-of-Understanding (PoU) Mathematical Ledger (BTC-grade difficulty & halving).
4. Grounded, Transparent Anti-Drift Self-Improvement Telemetry.
"""

from __future__ import annotations

import json
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
    recall_count INTEGER DEFAULT 0,
    origin TEXT DEFAULT 'distilled'
);
CREATE TABLE IF NOT EXISTS substrate_meta (
    key TEXT PRIMARY KEY,
    value TEXT
);
CREATE TABLE IF NOT EXISTS quests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT,
    title TEXT,
    context TEXT DEFAULT '',
    target INTEGER,
    progress INTEGER DEFAULT 0,
    reward REAL,
    status TEXT DEFAULT 'active',
    created_at REAL,
    expires_at REAL
);
CREATE INDEX IF NOT EXISTS idx_pou_timestamp ON pou_ledger(timestamp);
CREATE INDEX IF NOT EXISTS idx_pou_complexity ON pou_ledger(complexity);
CREATE INDEX IF NOT EXISTS idx_quests_status ON quests(status);
"""


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(str(db_path), timeout=30.0)


def _ensure_schema(db_path: Path) -> None:
    with _connect(db_path) as conn:
        conn.executescript(_SCHEMA)
        _ensure_fts(conn)
        _migrate_ledger_why(conn)
        conn.commit()


def _migrate_ledger_why(conn: sqlite3.Connection) -> None:
    """Add WHY-engine columns to pre-existing ledger tables (idempotent)."""
    cols = {row[1] for row in conn.execute("PRAGMA table_info(pou_ledger)").fetchall()}
    if "cause" not in cols:
        conn.execute("ALTER TABLE pou_ledger ADD COLUMN cause TEXT DEFAULT ''")
    if "hci" not in cols:
        conn.execute("ALTER TABLE pou_ledger ADD COLUMN hci REAL DEFAULT NULL")
    conn.execute(
        "UPDATE pou_ledger SET cause = COALESCE(NULLIF(cause, ''), 'legacy (pre-why)') "
        "WHERE cause IS NULL OR cause = ''"
    )
    # Substrate origin tracking for soul-sync versioning (idempotent).
    sub_cols = {row[1] for row in conn.execute("PRAGMA table_info(cognitive_memory_substrate)").fetchall()}
    if "origin" not in sub_cols:
        conn.execute("ALTER TABLE cognitive_memory_substrate ADD COLUMN origin TEXT DEFAULT 'distilled'")
    conn.execute(
        "CREATE TABLE IF NOT EXISTS substrate_meta (key TEXT PRIMARY KEY, value TEXT)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pou_timestamp ON pou_ledger(timestamp)"
    )
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_pou_complexity ON pou_ledger(complexity)"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS quests ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, type TEXT, title TEXT, "
        "context TEXT DEFAULT '', target INTEGER, progress INTEGER DEFAULT 0, "
        "reward REAL, status TEXT DEFAULT 'active', created_at REAL, expires_at REAL)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_quests_status ON quests(status)")


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
        metrics: PoUInteractionMetrics,
        *,
        cause: str = "",
    ) -> Dict[str, Any]:
        """Record turn metrics, update energy, compute leveling and persist.

        `cause` is a deterministic WHY-template string (never LLM-generated)
        explaining what triggered this exact delta. Stored verbatim so
        `hermes why` can trace every level change to its evidence.
        """
        now = time.time()
        with _connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT cumulative_energy, current_level, timestamp FROM pou_ledger "
                "ORDER BY id DESC LIMIT 1"
            )
            row = cur.fetchone()
            prev_energy = row[0] if row else 0.0
            prev_level = row[1] if row else 1
            last_ts = row[2] if row and row[2] else now

            cause_parts = [(cause or "unspecified").strip()[:400]]

            # LVL-3: lazy inactivity decay on stored energy (history untouched).
            idle_days = max(0.0, (now - last_ts) / 86400.0)
            if row and idle_days >= 1.0:
                decay = 0.5 ** (idle_days / INACTIVITY_HALVING_DAYS)
                if decay < 0.999:
                    prev_energy *= decay
                    cause_parts.append(
                        f"inactivity decay x{decay:.2f} ({idle_days:.1f}d idle)"
                    )

            energy_delta = self.calculate_energy_delta(metrics, prev_level)

            # LVL-2: anti-farming throttle on trivial-turn bursts (gains only).
            if energy_delta > 0:
                trivial_recent = cur.execute(
                    "SELECT COUNT(*) FROM pou_ledger WHERE timestamp > ? AND complexity <= ?",
                    (now - FARMING_WINDOW_SECONDS, AUTO_TURN_MAX_COMPLEXITY),
                ).fetchone()[0]
                if trivial_recent >= FARMING_TRIVIAL_COUNT:
                    energy_delta *= FARMING_GAIN_FACTOR
                    cause_parts.append(
                        f"farming-guard x{FARMING_GAIN_FACTOR} "
                        f"({trivial_recent} trivial turns/h)"
                    )

            # QUEST ENGINE: fold capped completion bonuses into this turn.
            try:
                _expire_quests(cur, now)
                _done, _bonus = _evaluate_quests(
                    cur, now, metrics, _substrate_max_id(cur)
                )
                if _bonus > 0:
                    energy_delta += _bonus
                    for _t, _r in _done:
                        cause_parts.append(f'quest done: "{_t}" +{_r:.0f}E')
            except Exception as _q_exc:
                logger.debug("Quest evaluation skipped: %s", _q_exc)

            new_energy = max(0.0, prev_energy + energy_delta)
            cause = " | ".join(cause_parts)[:500]

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

            turns_total = cur.execute("SELECT COUNT(*) FROM pou_ledger").fetchone()[0] + 1
            gates = promotion_gates(
                new_energy, next_target, hci, metrics.fatal_dissonance, turns_total
            )
            if all(gates.values()):
                new_level = prev_level + 1
            elif new_energy < current_target and prev_level > 1:
                # Demotion condition
                new_level = prev_level - 1
                
            cur.execute("""
                INSERT INTO pou_ledger (
                    timestamp, session_key, complexity, comprehension, soul_assimilation,
                    precision, satisfaction, energy_delta, cumulative_energy, current_level,
                    state_hash, cause, hci
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                now, session_key, metrics.task_complexity, metrics.master_comprehension,
                metrics.soul_assimilation, metrics.execution_precision, metrics.master_satisfaction,
                energy_delta, new_energy, new_level, "tier3-verified",
                cause, hci,
            ))
            # Quest generation on schedule (same transaction, after insert so
            # the new turn counts toward the cadence).
            new_quests: List[str] = []
            try:
                new_quests = _maybe_generate_quests(
                    cur, now, turns_total,
                    has_frustration_now=metrics.master_satisfaction < 0,
                )
            except Exception as _g_exc:
                logger.debug("Quest generation skipped: %s", _g_exc)
            conn.commit()

            if new_level != prev_level:
                direction = "UP" if new_level > prev_level else "DOWN"
                level_note = (
                    f"LEVEL {direction} {prev_level}->{new_level}: "
                    f"energy {new_energy:.1f} vs target {next_target:.1f} (next) / "
                    f"{current_target:.1f} (current), HCI {hci:.3f}"
                )
            else:
                blocked = [k for k, v in gates.items() if not v] if new_energy >= next_target else []
                block_txt = f" blocked by {','.join(blocked)}" if blocked else ""
                level_note = (
                    f"level held at {new_level}: energy {new_energy:.1f} / "
                    f"next target {next_target:.1f}, HCI {hci:.3f}{block_txt}"
                )

            return {
                "energy_delta": energy_delta,
                "cumulative_energy": new_energy,
                "current_level": new_level,
                "level_changed": (new_level != prev_level),
                "hci": hci,
                "cause": cause,
                "level_note": level_note,
                "gates": gates,
                "turns_total": turns_total,
                "new_quests": new_quests,
            }


def pou_status(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Current PoU standing for `hermes level` readout (read-only)."""
    path = Path(db_path) if db_path is not None else _default_db_path()
    if not path.exists():
        return {"turns": 0, "level": 1, "energy": 0.0, "effective_energy": 0.0,
                "next_target": CognitivePoULedger.difficulty_target(2),
                "progress_pct": 0.0, "hci": None, "last_cause": "no turns recorded yet",
                "idle_days": 0.0,
                "gates": {"energy_ok": False, "hci_ok": False, "no_fatal": True, "history_ok": False}}
    _ensure_schema(path)
    with _connect(path) as conn:
        cur = conn.cursor()
        turns = cur.execute("SELECT COUNT(*) FROM pou_ledger").fetchone()[0]
        row = cur.execute(
            "SELECT cumulative_energy, current_level, hci, cause, timestamp "
            "FROM pou_ledger ORDER BY id DESC LIMIT 1"
        ).fetchone()
    if not row:
        return {"turns": 0, "level": 1, "energy": 0.0, "effective_energy": 0.0,
                "next_target": CognitivePoULedger.difficulty_target(2),
                "progress_pct": 0.0, "hci": None, "last_cause": "no turns recorded yet",
                "idle_days": 0.0,
                "gates": {"energy_ok": False, "hci_ok": False, "no_fatal": True, "history_ok": False}}
    energy, level, hci, cause, last_ts = row
    target = CognitivePoULedger.difficulty_target(level + 1)
    idle_days = max(0.0, (time.time() - (last_ts or time.time())) / 86400.0)
    # Read-only projection: what the next record_turn would start from after
    # lazy decay (no mutation here — the ledger only changes on record).
    effective = energy * (0.5 ** (idle_days / INACTIVITY_HALVING_DAYS)) if idle_days >= 1.0 else energy
    gates = promotion_gates(energy, target, hci if hci is not None else 0.0, False, turns)
    return {"turns": turns, "level": level, "energy": energy,
            "effective_energy": effective,
            "next_target": target,
            "progress_pct": max(0.0, min(100.0, 100.0 * energy / target)),
            "hci": hci, "last_cause": cause or "unspecified",
            "idle_days": idle_days, "gates": gates}


def pou_why(limit: int = 10, db_path: Optional[Path] = None) -> List[str]:
    """Last-N ledger explanations for `hermes why` (read-only, deterministic).

    LVL-4 depth: rows are returned oldest-first with level-transition markers
    (e.g. ">>> LEVEL UP 1->2") plus the exact threshold math that decided it,
    so every promotion/demotion traces to numbers, not vibes.
    """
    path = Path(db_path) if db_path is not None else _default_db_path()
    if not path.exists():
        return ["No PoU turns recorded yet."]
    _ensure_schema(path)
    with _connect(path) as conn:
        rows = conn.execute(
            "SELECT timestamp, energy_delta, cumulative_energy, current_level, cause, hci "
            "FROM pou_ledger ORDER BY id DESC LIMIT ?",
            (max(1, min(50, limit)),),
        ).fetchall()
    if not rows:
        return ["No PoU turns recorded yet."]
    lines = []
    prev_level: Optional[int] = None
    for ts, delta, energy, level, cause, hci in reversed(rows):
        when = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts or 0))
        # ASCII-only: non-ASCII crashes Windows cp1252 consoles.
        hci_txt = f"{hci:.3f}" if hci is not None else "n/a"
        lines.append(
            f"[{when}] L{level} dE{delta:+.1f} (E={energy:.1f}, HCI={hci_txt}) "
            f"- {cause or 'unspecified'}"
        )
        if prev_level is not None and level != prev_level:
            direction = "UP" if level > prev_level else "DOWN"
            tgt = CognitivePoULedger.difficulty_target(level if direction == "UP" else prev_level)
            lines.append(
                f"  >>> LEVEL {direction} {prev_level}->{level} "
                f"(threshold math: E={energy:.1f} vs T={tgt:.1f}, HCI>={0.98})"
            )
        prev_level = level
    return list(reversed(lines))


# =============================================================================
# QUEST ENGINE — the leveling system gives missions to the agent (MC).
# Quests are born ONLY from real patterns in Tuan's prompts/tasks (a
# frustration cluster, a precision run, a learning drought) — never busywork.
# Bonuses are capped and one-time; penalties are never discounted.
# Every completion lands in the cause line, so `hermes why` shows it.
# =============================================================================

QUEST_REWARDS = {"streak": 100.0, "redemption": 80.0, "capture": 60.0}
QUEST_EXPIRY_DAYS = 14.0
QUEST_GENERATE_EVERY_TURNS = 20
QUEST_MAX_BONUS_PER_TURN = 150.0


def _quest_rows(cur: sqlite3.Cursor, status: str = "active") -> List[sqlite3.Row]:
    cur.execute(
        "SELECT id, type, title, context, target, progress, reward, status, "
        "created_at, expires_at FROM quests WHERE status = ? ORDER BY id",
        (status,),
    )
    return cur.fetchall()


def _expire_quests(cur: sqlite3.Cursor, now: float) -> int:
    cur.execute(
        "UPDATE quests SET status = 'expired' WHERE status = 'active' AND expires_at <= ?",
        (now,),
    )
    return cur.rowcount or 0


def _recent_frustrations(cur: sqlite3.Cursor, since_ts: float) -> int:
    row = cur.execute(
        "SELECT COUNT(*) FROM pou_ledger WHERE timestamp >= ? AND satisfaction < 0",
        (since_ts,),
    ).fetchone()
    return int(row[0]) if row else 0


def _substrate_max_id(cur: sqlite3.Cursor) -> int:
    try:
        row = cur.execute("SELECT MAX(id) FROM cognitive_memory_substrate").fetchone()
        return int(row[0]) if row and row[0] else 0
    except Exception:
        return 0


def _maybe_generate_quests(
    cur: sqlite3.Cursor, now: float, turns_total: int, has_frustration_now: bool
) -> List[str]:
    """Create at most one quest per free type slot (deterministic templates)."""
    created: List[str] = []
    if turns_total % QUEST_GENERATE_EVERY_TURNS != 0:
        return created
    active_types = set()
    try:
        for row in _quest_rows(cur):
            active_types.add(row[1])
    except Exception:
        return created

    def _add(qtype: str, title: str, context: str, target: int) -> None:
        cur.execute(
            "INSERT INTO quests (type, title, context, target, progress, reward, "
            "status, created_at, expires_at) VALUES (?, ?, ?, ?, 0, ?, 'active', ?, ?)",
            (qtype, title, context, target, QUEST_REWARDS[qtype], now,
             now + QUEST_EXPIRY_DAYS * 86400.0),
        )
        created.append(title)

    if "streak" not in active_types:
        _add("streak", "Precision streak: 5 turns at precision 1.0", "", 5)
    recent_bad = 0
    try:
        recent_bad = _recent_frustrations(cur, now - 7 * 86400.0)
    except Exception:
        recent_bad = 0
    if "redemption" not in active_types and (recent_bad >= 2 or has_frustration_now):
        _add("redemption", "Redemption: 3 turns with no corrections", "", 3)
    if "capture" not in active_types:
        try:
            grown = _substrate_max_id(cur)
        except Exception:
            grown = 0
        import json as _json

        _add("capture", "Capture: distill 1 durable learning in 10 turns",
             _json.dumps({"baseline_substrate_max_id": grown}), 1)
    return created


def _evaluate_quests(
    cur: sqlite3.Cursor,
    now: float,
    metrics: PoUInteractionMetrics,
    db_substrate_max_id: int,
) -> Tuple[List[Tuple[str, float]], float]:
    """Evaluate active quests against history + current turn.

    Returns (completed [(title, reward)], total_bonus capped). Progress
    persisted; completions marked done. Pure ledger reads + quest writes.
    """
    completed: List[Tuple[str, float]] = []
    bonus = 0.0
    try:
        active = _quest_rows(cur)
    except Exception:
        return completed, bonus
    for row in active:
        qid, qtype, title, context, target = row[0], row[1], row[2], row[3], row[4]
        done = False
        progress = 0
        try:
            created_at = float(row[8])
        except (TypeError, ValueError):
            created_at = now
        if qtype == "streak":
            progress = _streak_progress(cur, created_at, metrics)
            done = progress >= (target or 5)
        elif qtype == "redemption":
            progress = _redemption_progress(cur, created_at, metrics)
            done = progress >= (target or 3)
        elif qtype == "capture":
            baseline = 0
            try:
                import json as _json

                baseline = int(_json.loads(context or "{}").get("baseline_substrate_max_id", 0))
            except Exception:
                baseline = 0
            progress = 1 if db_substrate_max_id > baseline else 0
            done = progress >= (target or 1)
        else:
            continue
        cur.execute("UPDATE quests SET progress = ? WHERE id = ?", (progress, qid))
        if done:
            cur.execute("UPDATE quests SET status = 'done' WHERE id = ?", (qid,))
            reward = QUEST_REWARDS.get(qtype, 0.0)
            completed.append((title, reward))
            bonus += reward
    bonus = min(bonus, QUEST_MAX_BONUS_PER_TURN)
    return completed, bonus


def _streak_progress(cur: sqlite3.Cursor, created_at: float, metrics: PoUInteractionMetrics) -> int:
    vals = [metrics.execution_precision >= 1.0]
    try:
        rows = cur.execute(
            "SELECT precision FROM pou_ledger WHERE timestamp >= ? ORDER BY id DESC LIMIT 30",
            (created_at,),
        ).fetchall()
    except Exception:
        rows = []
    for row in rows:
        try:
            vals.append(float(row[0]) >= 1.0)
        except (TypeError, ValueError):
            vals.append(False)
    count = 0
    for v in vals:
        if v:
            count += 1
        else:
            break
    return count


def _redemption_progress(cur: sqlite3.Cursor, created_at: float, metrics: PoUInteractionMetrics) -> int:
    vals = [metrics.master_satisfaction >= 0]
    try:
        rows = cur.execute(
            "SELECT satisfaction FROM pou_ledger WHERE timestamp >= ? ORDER BY id DESC LIMIT 30",
            (created_at,),
        ).fetchall()
    except Exception:
        rows = []
    for row in rows:
        try:
            vals.append(float(row[0]) >= 0)
        except (TypeError, ValueError):
            vals.append(False)
    count = 0
    for v in vals:
        if v:
            count += 1
        else:
            break
    return count


def list_quests(db_path: Optional[Path] = None, include_done: int = 5) -> Dict[str, Any]:
    """Active quests + recent history for `hermes quests` (read-only)."""
    path = Path(db_path) if db_path is not None else _default_db_path()
    if not path.exists():
        return {"active": [], "recent": []}
    _ensure_schema(path)
    with _connect(path) as conn:
        cur = conn.cursor()
        try:
            active = [
                {"id": r[0], "type": r[1], "title": r[2], "target": r[4],
                 "progress": r[5], "reward": r[6]}
                for r in _quest_rows(cur)
            ]
            recent_rows = cur.execute(
                "SELECT title, status FROM quests WHERE status != 'active' "
                "ORDER BY id DESC LIMIT ?",
                (max(0, include_done),),
            ).fetchall()
            recent = [{"title": r[0], "status": r[1]} for r in recent_rows]
        except Exception:
            active, recent = [], []
    return {"active": active, "recent": recent}


def export_cognitive_state(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Export ledger + substrate + meta as a portable dict (VPS backup/migration).

    Read-only. Secrets are never stored in these tables, so the payload is
    safe to move between machines.
    """
    path = Path(db_path) if db_path is not None else _default_db_path()
    if not path.exists():
        return {"version": 1, "ledger": [], "substrate": [], "meta": {}}
    _ensure_schema(path)
    with _connect(path) as conn:
        cur = conn.cursor()
        cols = [r[1] for r in cur.execute("PRAGMA table_info(pou_ledger)").fetchall()]
        ledger_rows = [dict(zip(cols, r)) for r in cur.execute("SELECT * FROM pou_ledger ORDER BY id").fetchall()]
        scols = [r[1] for r in cur.execute("PRAGMA table_info(cognitive_memory_substrate)").fetchall()]
        sub_rows = [dict(zip(scols, r)) for r in cur.execute("SELECT * FROM cognitive_memory_substrate ORDER BY id").fetchall()]
        meta = dict(cur.execute("SELECT key, value FROM substrate_meta").fetchall())
    return {"version": 1, "ledger": ledger_rows, "substrate": sub_rows, "meta": meta}


def import_cognitive_state(payload: Dict[str, Any], db_path: Optional[Path] = None) -> Dict[str, int]:
    """Merge an exported payload into the local DB (VPS restore/migration).

    Ledger rows are appended as history (new ids); substrate rows merge by
    (topic, semantic_content) dedup so re-imports never duplicate; meta keys
    merge with incoming values winning. Returns counts per section.
    """
    if not isinstance(payload, dict) or payload.get("version") != 1:
        raise ValueError("unsupported cognitive-state payload (expected version 1)")
    path = Path(db_path) if db_path is not None else _default_db_path()
    _ensure_schema(path)
    counts = {"ledger": 0, "substrate": 0, "meta": 0}
    with _connect(path) as conn:
        cur = conn.cursor()
        for row in payload.get("ledger") or []:
            if not isinstance(row, dict):
                continue
            cur.execute("""
                INSERT INTO pou_ledger (
                    timestamp, session_key, complexity, comprehension, soul_assimilation,
                    precision, satisfaction, energy_delta, cumulative_energy, current_level,
                    state_hash, cause, hci
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row.get("timestamp", time.time()), str(row.get("session_key", "imported")),
                float(row.get("complexity", 0) or 0), float(row.get("comprehension", 0) or 0),
                float(row.get("soul_assimilation", 0) or 0), float(row.get("precision", 0) or 0),
                float(row.get("satisfaction", 0) or 0), float(row.get("energy_delta", 0) or 0),
                float(row.get("cumulative_energy", 0) or 0), int(row.get("current_level", 1) or 1),
                str(row.get("state_hash", "imported")), str(row.get("cause", "imported"))[:500],
                row.get("hci"),
            ))
            counts["ledger"] += 1
        for row in payload.get("substrate") or []:
            if not isinstance(row, dict):
                continue
            topic = str(row.get("topic", "")).strip()[:200]
            content = str(row.get("semantic_content", "")).strip()
            if not topic or not content:
                continue
            exists = cur.execute(
                "SELECT 1 FROM cognitive_memory_substrate WHERE topic = ? AND semantic_content = ? LIMIT 1",
                (topic, content),
            ).fetchone()
            if exists:
                continue
            try:
                importance = max(0.0, min(10.0, float(row.get("importance", 1.0))))
            except (TypeError, ValueError):
                importance = 1.0
            cur.execute("""
                INSERT INTO cognitive_memory_substrate (topic, semantic_content, importance, last_recalled, recall_count, origin)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                topic, content, importance, float(row.get("last_recalled", time.time()) or time.time()),
                int(row.get("recall_count", 0) or 0),
                str(row.get("origin", "distilled"))[:32] or "distilled",
            ))
            counts["substrate"] += 1
        for key, value in (payload.get("meta") or {}).items():
            cur.execute(
                "INSERT INTO substrate_meta (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (str(key), str(value)),
            )
            counts["meta"] += 1
        conn.commit()
    return counts


def conduct_advice(level: int, hci: Optional[float]) -> Dict[str, str]:
    """Advisory autonomy posture derived from PoU standing (pure, no I/O).

    LVL-5: maps level+HCI to how the agent should behave — junior confirms,
    senior acts — like a human professional ladder. ADVISORY ONLY: it never
    weakens safety gates; low standing can only add caution, never remove it.
    """
    lvl = max(1, int(level or 1))
    h = float(hci) if hci is not None else 0.0
    if lvl <= 1:
        posture = "junior"
        guidance = (
            "Show the plan before risky actions and confirm explicitly; "
            "prefer clarifying questions over guesses."
        )
    elif lvl == 2:
        posture = "associate"
        guidance = (
            "Execute routine tasks directly; present the plan first for "
            "multi-step or destructive-adjacent work."
        )
    else:
        posture = "senior"
        guidance = (
            "Execute autonomously within safety invariants; report compactly "
            "with evidence, flagging only genuine ambiguities."
        )
    if h < 0.80:
        guidance += " Caution override: HCI below 0.80 — verify understanding first."
        posture += "+cautious"
    return {"posture": posture, "guidance": guidance}


# =============================================================================
# 3. DYNAMIC SOUL ASSIMILATION & MEMORY DISTILLATION
# =============================================================================

class DynamicSoulMemorySubstrate:
    """Manages incremental absorption of SOUL.md into structured knowledge."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path is not None else _default_db_path()
        _ensure_schema(self.db_path)

    def distill_and_store(
        self, topic: str, content: str, importance: float = 1.0, origin: str = "distilled"
    ) -> Optional[int]:
        """Store semantic soul chunk into persistent cognitive memory substrate.

        Returns the new row id, or None when the input carries no content.
        `origin` tracks provenance: 'distilled' (learnings) vs 'soul-seed'
        (SOUL.md partitions, replaceable on reseed).
        """
        clean_topic = (topic or "").strip()[:200]
        clean_content = (content or "").strip()
        if not clean_topic or not clean_content:
            return None
        clean_origin = (origin or "distilled").strip()[:32] or "distilled"
        try:
            importance_val = max(0.0, min(10.0, float(importance)))
        except (TypeError, ValueError):
            importance_val = 1.0
        with _connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO cognitive_memory_substrate (topic, semantic_content, importance, last_recalled, origin)
                VALUES (?, ?, ?, ?, ?)
            """, (clean_topic, clean_content, importance_val, time.time(), clean_origin))
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

    @staticmethod
    def _rescore(
        rows: List[Tuple[int, str, str, float]],
        tokens: List[str],
    ) -> List[Tuple[float, int, str]]:
        """Rank candidates by IDF(token rarity) × importance × creation recency.

        - IDF down-weights ubiquitous words (e.g. "tuan" in every memory) so
          rare discriminative tokens decide — this fixed the measured MISS
          where FTS rank picked wrong memories sharing one common word.
        - Recency uses AUTOINCREMENT id order (higher = stored later) instead
          of last_recalled, avoiding a rich-get-richer recall feedback loop.
        Rows are (id, topic, semantic_content, importance).
        """
        import math as _math

        def _wordset(text: str) -> set:
            words = re.findall(r"\w+", text.lower())
            out = set(words)
            out.update(stem_indonesian(w) for w in words)
            return out

        N = max(1, len(rows))
        blobs = [(r[0], _wordset(r[1] + " " + r[2]), r[3]) for r in rows]
        # Query-side stems: match on the same stemmed space (df over the
        # expanded set so stems get honest document frequencies, not max IDF).
        qtokens = list({t for t in tokens} | {stem_indonesian(t) for t in tokens})
        df: Dict[str, int] = {}
        for t in set(qtokens):
            df[t] = sum(1 for _, words, _ in blobs if t in words)
        max_id = max((r[0] for r in rows), default=1)
        scored: List[Tuple[float, int, str]] = []
        by_id = {r[0]: (r[1], r[2]) for r in rows}
        for row_id, words, importance in blobs:
            token_score = sum(
                (_math.log(N / (1 + df.get(t, 0))) + 1.0) for t in qtokens if t in words
            )
            if token_score <= 0:
                continue
            recency = 0.9 + 0.2 * (row_id / max_id)
            final = token_score * (0.5 + importance) * recency
            topic, text = by_id[row_id]
            scored.append((final, row_id, f"[{topic}] {text}"))
        scored.sort(key=lambda x: x[0], reverse=True)
        return scored

    def query_relevant_soul_memory(self, task_context: str, limit: int = 3) -> List[str]:
        """Fetch JIT relevant memory: stem-expanded tokens → FTS5 → IDF rescoring.

        Short numeric tokens (e.g. "5", "404", "v2") are kept regardless of
        length — numbers are high-signal identifiers, and dropping them caused
        a measured 0.00 precision on numbered-procedure queries.
        """
        raw_tokens = [
            w.lower() for w in re.findall(r"\w+", task_context or "")
            if len(w) > 3 or w.isdigit()
        ]
        tokens = expand_query_tokens(raw_tokens)
        if not tokens:
            return []

        with _connect(self.db_path) as conn:
            # Primary path: FTS5 over-generates candidates, IDF rescoring picks.
            try:
                fts_query = " OR ".join(f'"{t}"' for t in tokens[:10])
                cur = conn.cursor()
                cur.execute("""
                    SELECT m.id, m.topic, m.semantic_content, m.importance
                    FROM cognitive_memory_fts f
                    JOIN cognitive_memory_substrate m ON m.id = f.rowid
                    WHERE cognitive_memory_fts MATCH ?
                    ORDER BY rank
                    LIMIT ?
                """, (fts_query, max(limit * 5, 15)))
                fts_rows = cur.fetchall()
                if fts_rows:
                    ranked = self._rescore(fts_rows, tokens)[:limit]
                    if ranked:
                        self._touch(conn, [r_id for _, r_id, _ in ranked])
                        conn.commit()
                        return [item[2] for item in ranked]
            except sqlite3.OperationalError as exc:
                logger.debug("FTS query failed, using fallback: %s", exc)

            # Fallback path: rescore the whole corpus identically.
            cur = conn.cursor()
            cur.execute(
                "SELECT id, topic, semantic_content, importance "
                "FROM cognitive_memory_substrate ORDER BY importance DESC"
            )
            rows = cur.fetchall()
            ranked = self._rescore(rows, tokens)[:limit]
            self._touch(conn, [r_id for _, r_id, _ in ranked])
            conn.commit()
            return [item[2] for item in ranked]

    @staticmethod
    def _touch(conn: sqlite3.Connection, row_ids: List[int]) -> None:
        now = time.time()
        for r_id in row_ids:
            conn.execute(
                "UPDATE cognitive_memory_substrate SET recall_count = recall_count + 1, "
                "last_recalled = ? WHERE id = ?",
                (now, r_id),
            )

    def count(self) -> int:
        """Number of stored substrate rows (used to seed once, never duplicate)."""
        try:
            with _connect(self.db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM cognitive_memory_substrate")
                row = cur.fetchone()
                return int(row[0]) if row else 0
        except Exception:
            return 0

    @staticmethod
    def soul_hash(soul_text: str) -> str:
        import hashlib as _hl

        return _hl.sha256((soul_text or "").encode("utf-8")).hexdigest()[:16]

    def ensure_soul_seeded(self, soul_text: str, max_chunks: int = 15) -> int:
        """Seed the substrate from SOUL.md, re-seeding when it changes.

        Writer side of the JIT loop: splits identity text by markdown headings
        into bounded topic chunks. Tracks a content hash in substrate_meta —
        when SOUL.md changes, only origin='soul-seed' rows are replaced while
        user-distilled learnings ('distilled') are never touched. Returns the
        number of chunks stored (0 when already in sync).
        """
        text = (soul_text or "").strip()
        if not text:
            return 0
        new_hash = self.soul_hash(text)
        with _connect(self.db_path) as conn:
            cur = conn.cursor()
            row = cur.execute(
                "SELECT value FROM substrate_meta WHERE key = 'soul_hash'"
            ).fetchone()
            old_hash = row[0] if row else None
            if old_hash == new_hash:
                still_there = cur.execute(
                    "SELECT COUNT(*) FROM cognitive_memory_substrate WHERE origin = 'soul-seed'"
                ).fetchone()[0]
                if still_there > 0:
                    return 0
            # Hash changed (or seeds missing): replace only soul-seed rows.
            cur.execute(
                "DELETE FROM cognitive_memory_substrate WHERE origin = 'soul-seed'"
            )
            conn.commit()
        chunks: List[Tuple[str, str]] = []
        current_topic = "SOUL Identity"
        current_lines: List[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            if stripped.startswith("##"):
                if current_lines:
                    chunks.append((current_topic, "\n".join(current_lines).strip()))
                    current_lines = []
                current_topic = stripped.lstrip("#").strip()[:200] or "SOUL Identity"
            elif stripped.startswith("#"):
                if current_lines:
                    chunks.append((current_topic, "\n".join(current_lines).strip()))
                    current_lines = []
                current_topic = stripped.lstrip("#").strip()[:200] or "SOUL Identity"
            else:
                current_lines.append(line)
        if current_lines:
            chunks.append((current_topic, "\n".join(current_lines).strip()))
        if not chunks:
            chunks = [("SOUL Identity", text)]
        stored = 0
        for topic, body in chunks[:max_chunks]:
            if not body:
                continue
            if self.distill_and_store(topic, body[:1500], importance=0.8, origin="soul-seed") is not None:
                stored += 1
        with _connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO substrate_meta (key, value) VALUES ('soul_hash', ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (new_hash,),
            )
            conn.commit()
        return stored


# Lightweight Indonesian stemmer for query expansion (no dependencies).
# Strips common affixes so "memeriksa"/"pemeriksaan"/"periksa" share the root
# "periksa", and "-nya"/"-ku"/"-mu" clitics. Applied to QUERY tokens only;
# stored content is untouched (safe, additive: original token always kept).
_ID_PREFIXES = ("meng", "meny", "men", "mem", "me", "peng", "peny", "pen", "pem", "per", "ber", "ter", "di", "ke", "se")
_ID_SUFFIXES = ("kan", "an", "i")
_ID_CLITICS = ("nya", "ku", "mu")


def stem_indonesian(word: str) -> str:
    """Return a crude root form of an Indonesian word (query-expansion use)."""
    w = (word or "").lower()
    for clitic in _ID_CLITICS:
        if len(w) > len(clitic) + 3 and w.endswith(clitic):
            w = w[: -len(clitic)]
            break
    for suffix in _ID_SUFFIXES:
        if len(w) > len(suffix) + 3 and w.endswith(suffix):
            w = w[: -len(suffix)]
            break
    for prefix in _ID_PREFIXES:
        if len(w) > len(prefix) + 3 and w.startswith(prefix):
            w = w[len(prefix):]
            break
    return w or word.lower()


def expand_query_tokens(tokens: List[str]) -> List[str]:
    """Original tokens plus stemmed variants (deduped, order-stable)."""
    expanded: List[str] = []
    for t in tokens:
        if t not in expanded:
            expanded.append(t)
        stem = stem_indonesian(t)
        if stem != t and stem not in expanded:
            expanded.append(stem)
    return expanded


def compact_identity_pointer(chunk_count: int) -> str:
    """Tiny stable-prompt pointer replacing a re-dumped identity file.

    Used only when HERMES_TIER3_COMPACT_IDENTITY=1 and the substrate already
    holds the seeded identity: ~60 chars instead of up to 20_000 (~40-300x
    on the identity line-item), with JIT memories carrying the substance.
    """
    return (
        f"[Identity assimilated into memory substrate ({chunk_count} chunks); "
        f"relevant partitions recalled just-in-time below.]"
    )


# Maximum complexity an automatically derived turn may carry. Auto turns use
# real tool-execution signals but neutral judgment values, so the cap keeps
# them informative without ever inflating leveling on their own.
AUTO_TURN_MAX_COMPLEXITY = 0.15

# Anti-farming guard: a burst of trivial auto turns inside one hour gets its
# gains throttled (never its penalties — accountability is never discounted).
FARMING_WINDOW_SECONDS = 3600.0
FARMING_TRIVIAL_COUNT = 30
FARMING_GAIN_FACTOR = 0.5

# Inactivity decay: stored energy halves per full idle period (lazy, applied
# on record, always disclosed in the cause line). Keeps levels earned, not
# parked — without wiping history (rows are never deleted).
INACTIVITY_HALVING_DAYS = 30.0

# Promotion requires a minimum evidence history so a single lucky turn can
# never promote on noise. Demotion has no such floor (accountability first).
MIN_TURNS_FOR_PROMOTION = 5


def promotion_gates(
    energy: float, next_target: float, hci: float, fatal_dissonance: bool, turns_total: int
) -> Dict[str, bool]:
    """Evaluate each promotion gate independently (pure, testable).

    Returned mapping tells exactly which gate holds a promotion back, so
    `hermes level` never shows a confusing "100% but no level-up" again.
    """
    return {
        "energy_ok": energy >= next_target,
        "hci_ok": hci >= 0.98,
        "no_fatal": not fatal_dissonance,
        "history_ok": turns_total >= MIN_TURNS_FOR_PROMOTION,
    }


def _turn_tool_stats(messages: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Count (successful, total) tool calls since the last user message.

    Tool content is JSON with a "success" flag when structured, plain text
    otherwise (counted as success — the turn cap bounds any inflation).
    """
    start = 0
    for idx, msg in enumerate(messages or []):
        if isinstance(msg, dict) and msg.get("role") == "user":
            start = idx + 1
    success = 0
    total = 0
    for msg in (messages or [])[start:]:
        if not isinstance(msg, dict) or msg.get("role") != "tool":
            continue
        total += 1
        content = msg.get("content", "")
        try:
            data = json.loads(content) if isinstance(content, str) else content
            if isinstance(data, dict) and data.get("success") is False:
                continue
        except Exception:
            pass
        success += 1
    return success, total


def record_turn_event(
    session_key: str,
    messages: List[Dict[str, Any]],
    *,
    completed: bool,
    interrupted: bool,
    is_review_fork: bool = False,
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Record one conservative per-turn PoU event (event-driven density).

    Uses only measured signals: tool success ratio from this turn's tool
    messages. Judgment fields stay neutral (satisfaction 0.0) and complexity
    is capped by AUTO_TURN_MAX_COMPLEXITY, so auto turns densify the ledger
    (~10-50x more events than review-gated recording) without inflating it.
    Skipped for interrupted turns and background-review forks.
    """
    try:
        if interrupted or is_review_fork:
            return None
        success, total = _turn_tool_stats(messages)
        if total == 0 and not completed:
            return None
        precision = (success / total) if total > 0 else 0.6
        metrics = PoUInteractionMetrics(
            task_complexity=min(AUTO_TURN_MAX_COMPLEXITY, 0.03 + 0.01 * total),
            master_comprehension=0.7,
            soul_assimilation=0.5,
            execution_precision=precision,
            master_satisfaction=0.0,
        )
        cause = (
            f"auto-turn: {success}/{total} tools ok "
            f"(precision {precision:.2f}), neutral judgment, "
            f"complexity capped at {AUTO_TURN_MAX_COMPLEXITY}"
        )
        return get_tier3_ledger(db_path).record_turn(session_key or "default", metrics, cause=cause)
    except Exception as exc:
        logger.debug("PoU turn-event recording skipped: %s", exc)
        return None


# Frustration phrases indicating the agent missed user intent. Used only to
# derive conservative auto-metrics for the PoU ledger — never shown to users.
_FRUSTRATION_PHRASES = (
    "stop doing",
    "too verbose",
    "don't format",
    "do not format",
    "why are you explaining",
    "just give me the answer",
    "you always do",
    "i hate",
    "that's wrong",
    "that is wrong",
    "you misunderstood",
    "not what i asked",
    "useless",
)


def record_session_review_outcome(
    session_key: str,
    messages_snapshot: List[Dict[str, Any]],
    actions: List[str],
    db_path: Optional[Path] = None,
) -> Optional[Dict[str, Any]]:
    """Record one conservative PoU turn from background-review signals.

    This is the production writer for the PoU ledger: frustration phrases in
    user messages become a low-satisfaction turn, a clean session with saved
    learnings becomes a modest positive turn. Complexity is capped low so
    auto-derived turns can never inflate leveling — strong turns only come
    from explicit, verified achievements.
    """
    try:
        user_texts = [
            str(m.get("content", ""))
            for m in (messages_snapshot or [])
            if isinstance(m, dict) and m.get("role") == "user"
        ]
        turns = max(1, len(user_texts))
        hits = sum(
            1
            for phrase in _FRUSTRATION_PHRASES
            for text in user_texts
            if phrase in text.lower()
        )
        if hits > 0:
            metrics = PoUInteractionMetrics(
                task_complexity=min(0.5, 0.2 + 0.02 * turns),
                master_comprehension=0.4,
                soul_assimilation=0.5,
                execution_precision=0.5,
                master_satisfaction=-0.6,
            )
            cause = (
                f"review: {hits} frustration signal(s) in {turns} user turn(s), "
                f"quadratic slash applied"
            )
        elif actions:
            metrics = PoUInteractionMetrics(
                task_complexity=min(0.4, 0.15 + 0.02 * turns),
                master_comprehension=0.8,
                soul_assimilation=0.6,
                execution_precision=0.7,
                master_satisfaction=0.4,
            )
            cause = (
                f"review: no corrections, {len(actions)} learning action(s) saved "
                f"over {turns} user turn(s)"
            )
        else:
            metrics = PoUInteractionMetrics(
                task_complexity=0.1,
                master_comprehension=0.75,
                soul_assimilation=0.5,
                execution_precision=0.6,
                master_satisfaction=0.1,
            )
            cause = "review: quiet session, no corrections, no new learnings"
        return get_tier3_ledger(db_path).record_turn(session_key or "default", metrics, cause=cause)
    except Exception as exc:
        logger.debug("PoU review-outcome recording skipped: %s", exc)
        return None


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
