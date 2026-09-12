"""Secondary tier matrix T1-T5 with refuse-start validation.

T1: read-only status queries only.
T2: T1 + non-destructive lookups.
T3: T2 + limited actions explicitly allowlisted.
T4: T3 + broader actions with operator confirmation path.
T5: full agent capability (requires explicit operator opt-in).

Refuse-start: invalid tier or missing required fields -> errors list,
caller must refuse to start the secondary channel.
"""

from __future__ import annotations

from typing import Any

VALID_TIERS = ("T1", "T2", "T3", "T4", "T5")

SECONDARY_TIERS: dict[str, dict[str, Any]] = {
    "T1": {
        "description": "Read-only status queries.",
        "allow_actions": False,
        "allow_tools": False,
        "requires_totp": True,
    },
    "T2": {
        "description": "T1 + non-destructive lookups.",
        "allow_actions": False,
        "allow_tools": True,
        "requires_totp": True,
    },
    "T3": {
        "description": "T2 + limited allowlisted actions.",
        "allow_actions": True,
        "allow_tools": True,
        "requires_totp": True,
    },
    "T4": {
        "description": "T3 + broader actions with confirmation.",
        "allow_actions": True,
        "allow_tools": True,
        "requires_totp": True,
        "requires_confirmation": True,
    },
    "T5": {
        "description": "Full agent capability. Explicit opt-in only.",
        "allow_actions": True,
        "allow_tools": True,
        "requires_totp": True,
        "requires_confirmation": True,
        "requires_explicit_opt_in": True,
    },
}


def get_tier(tier: str) -> dict[str, Any] | None:
    """Return the tier descriptor, or None for unknown tiers."""
    key = str(tier or "").strip().upper()
    entry = SECONDARY_TIERS.get(key)
    return dict(entry) if entry else None


def validate_secondary_config(cfg: dict[str, Any] | None) -> list[str]:
    """Validate the ``secondary`` config block. Returns error list (empty = OK).

    Refuse-start contract: the caller must refuse to start the secondary
    channel when this returns a non-empty list. Never auto-corrects.
    """
    errors: list[str] = []
    cfg = cfg or {}
    if not isinstance(cfg, dict):
        return ["secondary: must be a mapping"]
    if not cfg.get("enabled", False):
        return []  # disabled -> nothing to validate
    tier = str(cfg.get("tier") or "").strip().upper()
    if tier not in VALID_TIERS:
        errors.append(f"secondary.tier must be one of {list(VALID_TIERS)}, got {cfg.get('tier')!r}")
        return errors
    if not str(cfg.get("primary_channel") or "").strip():
        errors.append("secondary.primary_channel is required when secondary.enabled=true")
    if tier == "T5" and not cfg.get("t5_explicit_opt_in", False):
        errors.append("secondary T5 requires secondary.t5_explicit_opt_in=true")
    totp_required = cfg.get("totp_required", True)
    if totp_required not in (True, False):
        errors.append("secondary.totp_required must be a boolean")
    enforce = cfg.get("single_provider_enforce", False)
    if enforce not in (True, False):
        errors.append("secondary.single_provider_enforce must be a boolean")
    return errors
