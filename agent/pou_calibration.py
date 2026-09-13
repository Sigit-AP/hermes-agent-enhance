"""Read-only PoU ledger calibration reporter for Hermes Agent.

Pure reader over the ``pou_ledger`` table owned by
:mod:`agent.tier3_cognitive_core`. This module NEVER writes to the
database (opens SQLite in read-only URI mode + ``PRAGMA query_only``)
and NEVER mutates constants — it only snapshots them into the
recommendations for human review.

All recommendation strings are ASCII-only (Windows cp1252 consoles).
"""

from __future__ import annotations

import math
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from agent.tier3_cognitive_core import (
    AUTO_TURN_MAX_COMPLEXITY,
    ENERGY_SCALE,
    FARMING_GAIN_FACTOR,
    FARMING_TRIVIAL_COUNT,
    FARMING_WINDOW_SECONDS,
    INACTIVITY_HALVING_DAYS,
    MIN_TURNS_FOR_PROMOTION,
    POU_HISTORY_WINDOW,
)


def _constants_snapshot() -> str:
    """One-line ASCII snapshot of the live calibration constants."""
    return (
        "constants: ENERGY_SCALE=%.1f POU_HISTORY_WINDOW=%d "
        "MIN_TURNS_FOR_PROMOTION=%d FARMING_TRIVIAL_COUNT=%d "
        "FARMING_GAIN_FACTOR=%.2f FARMING_WINDOW_SECONDS=%.1f "
        "INACTIVITY_HALVING_DAYS=%.1f AUTO_TURN_MAX_COMPLEXITY=%.2f"
        % (
            float(ENERGY_SCALE),
            int(POU_HISTORY_WINDOW),
            int(MIN_TURNS_FOR_PROMOTION),
            int(FARMING_TRIVIAL_COUNT),
            float(FARMING_GAIN_FACTOR),
            float(FARMING_WINDOW_SECONDS),
            float(INACTIVITY_HALVING_DAYS),
            float(AUTO_TURN_MAX_COMPLEXITY),
        )
    )


def _constants_dict() -> Dict[str, float]:
    """Numeric snapshot of the live calibration constants (copies only)."""
    return {
        "ENERGY_SCALE": float(ENERGY_SCALE),
        "POU_HISTORY_WINDOW": int(POU_HISTORY_WINDOW),
        "MIN_TURNS_FOR_PROMOTION": int(MIN_TURNS_FOR_PROMOTION),
        "FARMING_TRIVIAL_COUNT": int(FARMING_TRIVIAL_COUNT),
        "FARMING_GAIN_FACTOR": float(FARMING_GAIN_FACTOR),
        "FARMING_WINDOW_SECONDS": float(FARMING_WINDOW_SECONDS),
        "INACTIVITY_HALVING_DAYS": float(INACTIVITY_HALVING_DAYS),
        "AUTO_TURN_MAX_COMPLEXITY": float(AUTO_TURN_MAX_COMPLEXITY),
    }


def calibration_report(db_path: Optional[Path] = None) -> Dict[str, Any]:
    """Build a read-only calibration report from the PoU ledger.

    Args:
        db_path: Path to ``cognitive_state.db``. ``None`` is treated as
            "no data" (never touches the default home DB).

    Returns:
        Dict with turns, level_histogram, mean/std of energy_delta,
        mean_hci, promotion/demotion counts, cause-marker hit counts,
        days_span, constants snapshot, and recommendations. When the
        table is missing/unreadable returns
        ``{"turns": 0, "recommendations": []}``.

    Read-only: opens SQLite via ``mode=ro`` URI plus ``PRAGMA
    query_only = ON``; issues SELECT statements only.
    """
    if db_path is None:
        return {"turns": 0, "recommendations": []}
    path = Path(db_path)
    try:
        uri = path.resolve().as_uri() + "?mode=ro"
        conn = sqlite3.connect(uri, uri=True, timeout=30.0)
    except Exception:
        return {"turns": 0, "recommendations": []}
    try:
        try:
            conn.execute("PRAGMA query_only = ON")
        except Exception:
            pass
        try:
            exists = conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type = 'table' AND name = 'pou_ledger'"
            ).fetchone()
        except Exception:
            return {"turns": 0, "recommendations": []}
        if not exists:
            return {"turns": 0, "recommendations": []}
        rows = conn.execute(
            "SELECT energy_delta, current_level, hci, cause, timestamp "
            "FROM pou_ledger ORDER BY id"
        ).fetchall()
    except Exception:
        return {"turns": 0, "recommendations": []}
    finally:
        try:
            conn.close()
        except Exception:
            pass

    turns = len(rows)
    if turns == 0:
        return {"turns": 0, "recommendations": []}

    levels: List[int] = []
    deltas: List[float] = []
    hcis: List[float] = []
    causes: List[str] = []
    stamps: List[float] = []
    for energy_delta, level, hci, cause, timestamp in rows:
        try:
            deltas.append(float(energy_delta))
        except (TypeError, ValueError):
            deltas.append(0.0)
        try:
            levels.append(int(level))
        except (TypeError, ValueError):
            levels.append(1)
        if hci is not None:
            try:
                hcis.append(float(hci))
            except (TypeError, ValueError):
                pass
        causes.append(str(cause or ""))
        if timestamp is not None:
            try:
                stamps.append(float(timestamp))
            except (TypeError, ValueError):
                pass

    histogram: Dict[int, int] = {}
    for lvl in levels:
        histogram[lvl] = histogram.get(lvl, 0) + 1

    mean_delta = sum(deltas) / len(deltas)
    var = sum((d - mean_delta) ** 2 for d in deltas) / len(deltas)
    std_delta = math.sqrt(var) if var > 0 else 0.0
    mean_hci = (sum(hcis) / len(hcis)) if hcis else 0.0

    promotions = sum(1 for prev, cur in zip(levels, levels[1:]) if cur > prev)
    demotions = sum(1 for prev, cur in zip(levels, levels[1:]) if cur < prev)
    farming_hits = sum(1 for c in causes if "farming-guard" in c)
    decay_hits = sum(1 for c in causes if "inactivity decay" in c)
    quest_hits = sum(1 for c in causes if "quest done" in c)
    days_span = ((max(stamps) - min(stamps)) / 86400.0) if len(stamps) >= 2 else 0.0

    recommendations: List[str] = []
    if turns < 50:
        recommendations.append("collect more data: %d/50 turns" % turns)
    if turns >= 20 and mean_delta <= 0:
        recommendations.append(
            "energy mean non-positive: consider raising ENERGY_SCALE"
        )
    if turns >= 100 and promotions == 0:
        recommendations.append("no promotions in 100+ turns: review T0/curve")
    if turns >= 30 and demotions > promotions:
        recommendations.append("demotions exceed promotions: check penalty kappa")
    if farming_hits > 0:
        recommendations.append(
            "farming guard active (%d hits): healthy" % farming_hits
        )
    recommendations.append(_constants_snapshot())

    return {
        "turns": turns,
        "level_histogram": histogram,
        "mean_delta": mean_delta,
        "std_delta": std_delta,
        "mean_hci": mean_hci,
        "promotions": promotions,
        "demotions": demotions,
        "farming_hits": farming_hits,
        "decay_hits": decay_hits,
        "quest_hits": quest_hits,
        "days_span": days_span,
        "constants": _constants_dict(),
        "recommendations": recommendations,
    }
