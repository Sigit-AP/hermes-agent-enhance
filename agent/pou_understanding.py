"""Per-turn comprehension signals (Proof-of-Understanding input).

Pure functions only: no I/O, no DB, no imports beyond stdlib.
Replaces neutral 0.7/0.75 judgment estimates with measured signals
derived from correction phrases, tool retry/error rate, and turn
completion state.

All strings ASCII-only (Windows cp1252 console safety).
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

CORRECTION_PHRASES: Tuple[str, ...] = (
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

_ERROR_RE = re.compile(r"error|failed|traceback|exception", re.IGNORECASE)


def count_corrections(user_texts: List[str]) -> int:
    """Count user texts containing at least one correction phrase.

    Case-insensitive substring match. Non-string entries are skipped.
    """
    count = 0
    for text in user_texts or []:
        if not isinstance(text, str):
            continue
        lowered = text.lower()
        for phrase in CORRECTION_PHRASES:
            if phrase in lowered:
                count += 1
                break
    return count


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content)
    except Exception:
        return str(content)


def tool_retry_stats(messages: List[Dict[str, Any]]) -> Tuple[int, int]:
    """Return (errors, total) for tool-role messages since last user msg.

    A tool msg counts as error when its JSON content has success===False
    or its text matches /error|failed|traceback|exception/i.
    Non-JSON content counts as success (matches _turn_tool_stats).
    Malformed JSON falls back to text matching.
    """
    msgs = messages or []
    start = 0
    for idx, msg in enumerate(msgs):
        if isinstance(msg, dict) and msg.get("role") == "user":
            start = idx + 1
    errors = 0
    total = 0
    for msg in msgs[start:]:
        if not isinstance(msg, dict) or msg.get("role") != "tool":
            continue
        total += 1
        content = msg.get("content", "")
        text = _content_text(content)
        is_error = False
        if isinstance(content, str):
            try:
                data = json.loads(content)
            except Exception:
                data = None
            if isinstance(data, dict) and data.get("success") is False:
                is_error = True
            elif _ERROR_RE.search(text):
                is_error = True
        else:
            if isinstance(content, dict) and content.get("success") is False:
                is_error = True
            elif _ERROR_RE.search(text):
                is_error = True
        if is_error:
            errors += 1
    return errors, total


def _user_texts(messages: List[Dict[str, Any]]) -> List[str]:
    texts: List[str] = []
    for msg in messages or []:
        if not isinstance(msg, dict) or msg.get("role") != "user":
            continue
        content = msg.get("content", "")
        if isinstance(content, str):
            texts.append(content)
        else:
            texts.append(_content_text(content))
    return texts


def measure_turn_understanding(
    messages: List[Dict[str, Any]],
    completed: bool,
    interrupted: bool,
) -> Dict[str, Any]:
    """Measure per-turn comprehension from observable signals.

    comprehension: starts 0.85, -0.15 per correction, floor 0.1.
    satisfaction: -0.6 if any correction; else 0.2 if completed else 0.0;
        overridden to -0.3 when interrupted.
    precision_hint: 1 - errors/total over tool msgs, or None if no tools.
    """
    corrections = count_corrections(_user_texts(messages))
    errors, total = tool_retry_stats(messages)
    comprehension = max(0.1, 0.85 - 0.15 * corrections)
    if corrections > 0:
        satisfaction = -0.6
    else:
        satisfaction = 0.2 if completed else 0.0
    if interrupted:
        satisfaction = -0.3
    precision_hint: Optional[float] = None
    if total > 0:
        precision_hint = 1.0 - (errors / total)
    return {
        "comprehension": comprehension,
        "satisfaction": satisfaction,
        "precision_hint": precision_hint,
    }
