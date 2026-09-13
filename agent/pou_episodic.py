"""Episodic WHY-memory: turn summaries chained to ledger row ids.

Pure stdlib (sqlite3 only). All stored/returned strings are ASCII-only
so Windows cp1252 consoles never crash on print.
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

_DBPath = Union[str, Path]


def _resolve_db(db_path: _DBPath) -> Path:
    """Resolve None to the default home DB (never a file literally named 'None')."""
    if db_path is None:
        import os

        home = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
        home.mkdir(parents=True, exist_ok=True)
        return home / "cognitive_state.db"
    return Path(db_path)


def get_episode(db_path: _DBPath, ledger_id: int) -> Optional[str]:
    """Fetch one episode summary by ledger row id (for `why --episodes`)."""
    try:
        lid = int(ledger_id)
    except Exception:
        return None
    try:
        with sqlite3.connect(str(_resolve_db(db_path)), timeout=30.0) as conn:
            _ensure(conn)
            row = conn.execute(
                "SELECT summary FROM turn_episodes WHERE ledger_id = ?", (lid,)
            ).fetchone()
            return _ascii(row[0]) if row else None
    except Exception:
        return None


def _ascii(text: Any) -> str:
    try:
        s = "" if text is None else str(text)
    except Exception:
        return ""
    return s.encode("ascii", errors="ignore").decode("ascii")


def _ensure(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS turn_episodes ("
        "ledger_id INTEGER PRIMARY KEY, "
        "session_key TEXT, "
        "timestamp REAL, "
        "summary TEXT, "
        "tools_ok INTEGER, "
        "tools_total INTEGER, "
        "completed INTEGER)"
    )


def _first_user_text(messages: Any) -> str:
    try:
        items = list(messages) if messages else []
    except Exception:
        return ""
    for m in items:
        try:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role", ""))
            if role != "user":
                continue
            content = m.get("content")
            if isinstance(content, str) and content.strip():
                return _ascii(content.strip())
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and isinstance(
                        part.get("text"), str
                    ) and part["text"].strip():
                        return _ascii(part["text"].strip())
        except Exception:
            continue
    return ""


def summarize_turn(
    messages: List[Dict[str, Any]],
    final_response: str,
    max_chars: int = 300,
) -> str:
    """Deterministic extractive summary (no LLM).

    Template: first user text (<=120 chars) + " | tools ok/total"
    + first 80 chars of final response. Never empty.
    """
    try:
        limit = max(1, int(max_chars))
    except Exception:
        limit = 300
    user_txt = _ascii(_first_user_text(messages))[:120].strip()
    resp_txt = _ascii(final_response).strip().replace("\n", " ")[:80].strip()
    if not user_txt and not resp_txt:
        return "quiet turn"
    tools_ok = 0
    tools_total = 0
    try:
        items = list(messages) if messages else []
        for m in items:
            if isinstance(m, dict) and m.get("role") == "tool":
                tools_total += 1
                c = m.get("content")
                if isinstance(c, str) and "error" not in c.lower():
                    tools_ok += 1
    except Exception:
        pass
    summary = "%s | tools %d/%d | %s" % (user_txt, tools_ok, tools_total, resp_txt)
    summary = " ".join(summary.split())
    if not summary:
        return "quiet turn"
    return _ascii(summary)[:limit]


def record_episode(
    db_path: _DBPath,
    ledger_id: int,
    session_key: str,
    messages: List[Dict[str, Any]],
    final_response: str,
    tools_ok: int,
    tools_total: int,
    completed: bool,
) -> Optional[int]:
    """Persist one episode row keyed by ledger_id. Returns ledger_id or None."""
    try:
        lid = int(ledger_id)
    except Exception:
        return None
    try:
        summary = summarize_turn(messages, final_response)
        if not summary:
            return None
        try:
            ok = max(0, int(tools_ok))
        except Exception:
            ok = 0
        try:
            total = max(0, int(tools_total))
        except Exception:
            total = 0
        done = 1 if completed else 0
        sk = _ascii(session_key)
        with sqlite3.connect(str(_resolve_db(db_path)), timeout=30.0) as conn:
            _ensure(conn)
            conn.execute(
                "INSERT OR REPLACE INTO turn_episodes "
                "(ledger_id, session_key, timestamp, summary, "
                "tools_ok, tools_total, completed) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (lid, sk, time.time(), summary, ok, total, done),
            )
            conn.commit()
        return lid
    except Exception:
        return None


def episodic_recall(
    db_path: _DBPath, query: str, limit: int = 3
) -> List[str]:
    """Substring match over summaries (case-insensitive)."""
    q = _ascii(query).strip().lower()
    if not q:
        return []
    try:
        n = max(1, int(limit))
    except Exception:
        n = 3
    try:
        with sqlite3.connect(str(_resolve_db(db_path)), timeout=30.0) as conn:
            _ensure(conn)
            cur = conn.cursor()
            cur.execute(
                "SELECT ledger_id, summary FROM turn_episodes "
                "ORDER BY ledger_id DESC"
            )
            rows = cur.fetchall() or []
    except Exception:
        return []
    out: List[str] = []
    for lid, summary in rows:
        try:
            s = _ascii(summary)
            if q in s.lower():
                out.append("[turn #%s] %s" % (lid, s))
                if len(out) >= n:
                    break
        except Exception:
            continue
    return out
