"""PoU conduct posture block — pure, enforced-but-safe prompt posture.

Pure functions only: no I/O, no DB, no imports beyond stdlib types.
All strings ASCII-only (Windows cp1252 console safety).
Safety: this module only appends caution; it never weakens approvals/denials.
"""

from __future__ import annotations

from typing import Optional


def _base_posture(level: int) -> str:
    try:
        lvl = int(level)
    except (TypeError, ValueError):
        lvl = 1
    if lvl <= 1:
        return "junior"
    if lvl == 2:
        return "associate"
    return "senior"


def posture_for(level: int, hci: Optional[float] = None) -> str:
    """Map PoU level (+HCI) to a posture label.

    Base: lvl<=1 junior; ==2 associate; >=3 senior.
    Suffix "+cautious" when hci is not None and hci < 0.80.
    """
    base = _base_posture(level)
    try:
        if hci is not None and float(hci) < 0.80:
            return base + "+cautious"
    except (TypeError, ValueError):
        pass
    return base


def should_clarify_first(level: int, hci: Optional[float], task_complexity: float) -> bool:
    """Return True when the turn should clarify before acting."""
    if _base_posture(level) == "junior":
        return True
    try:
        if hci is not None and float(hci) < 0.80:
            return True
    except (TypeError, ValueError):
        pass
    try:
        complexity = float(task_complexity)
    except (TypeError, ValueError):
        complexity = 0.0
    try:
        lvl = int(level)
    except (TypeError, ValueError):
        lvl = 1
    if complexity >= 0.7 and lvl < 3:
        return True
    return False


_RULES = {
    "junior": "Confirm scope before mutating; ask when ambiguous.",
    "associate": "Execute routine tasks directly; confirm destructive-adjacent ones first.",
    "senior": "Execute directly; report compactly on completion.",
}


def conduct_posture_block(level: int, hci: Optional[float], recent_corrections: int) -> str:
    """Build a short ASCII posture block (<=600 chars)."""
    posture = posture_for(level, hci)
    base = posture.split("+")[0]
    rule = _RULES.get(base, _RULES["junior"])
    try:
        corr = int(recent_corrections)
    except (TypeError, ValueError):
        corr = 0
    if corr < 0:
        corr = 0
    try:
        hci_txt = f"{float(hci):.2f}" if hci is not None else "n/a"
    except (TypeError, ValueError):
        hci_txt = "n/a"
    try:
        lvl_txt = str(int(level))
    except (TypeError, ValueError):
        lvl_txt = "1"
    block = "[Posture: %s] Level %s HCI %s. %s" % (posture, lvl_txt, hci_txt, rule)
    if "+cautious" in posture:
        block += " Extra caution: consistency is low, double-check assumptions."
    if corr > 0:
        block += " Caution: %d recent correction(s) observed; restate plan before acting." % corr
    if len(block) > 600:
        block = block[:600]
    return block
