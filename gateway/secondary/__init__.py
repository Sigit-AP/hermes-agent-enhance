"""Secondary gateway package (HONEST-ONLY).

Polls PairingStore for approval state. Never approves on its own.
Approval happens only via the primary channel (hermes pairing approve).
"""

from gateway.secondary.gate import SecondaryGate, is_secondary_allowed
from gateway.secondary.tiers import (
    SECONDARY_TIERS,
    VALID_TIERS,
    get_tier,
    validate_secondary_config,
)
from gateway.secondary.origin import OriginTag, tag_origin
from gateway.secondary.audit import (
    append_audit_event,
    take_config_snapshot,
    rollback_snapshot_if_recent,
)

__all__ = [
    "SecondaryGate",
    "is_secondary_allowed",
    "SECONDARY_TIERS",
    "VALID_TIERS",
    "get_tier",
    "validate_secondary_config",
    "OriginTag",
    "tag_origin",
    "append_audit_event",
    "take_config_snapshot",
    "rollback_snapshot_if_recent",
]
