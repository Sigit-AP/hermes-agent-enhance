"""Secondary gate: poll approval state, never approve.

The secondary channel may NOT approve users itself. Approval happens only
via the primary channel (``hermes pairing approve <platform> <code>``).
This module only *reads* :meth:`PairingStore.is_approved`.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

logger = logging.getLogger(__name__)


class _ApprovalPoller(Protocol):
    def is_approved(self, platform: str, user_id: str) -> bool: ...


def is_secondary_allowed(
    secondary_cfg: dict[str, Any] | None,
    pairing_store: _ApprovalPoller | None,
    platform: str,
    user_id: str,
) -> bool:
    """Return True only when secondary is enabled AND user is approved.

    Fail-closed: any missing config, missing store, empty ids -> False.
    No approval is ever granted here; this polls existing approval state.
    """
    if not secondary_cfg or not secondary_cfg.get("enabled", False):
        return False
    if pairing_store is None:
        return False
    platform = str(platform or "").strip()
    user_id = str(user_id or "").strip()
    if not platform or not user_id:
        return False
    try:
        return bool(pairing_store.is_approved(platform, user_id))
    except Exception as exc:
        logger.warning("SecondaryGate poll failed for %s: %s", platform, exc)
        return False


class SecondaryGate:
    """Thin wrapper around :func:`is_secondary_allowed`.

    Intentionally exposes no ``approve`` method. Use the primary channel.
    """

    def __init__(self, secondary_cfg: dict[str, Any] | None, pairing_store: _ApprovalPoller | None):
        self._cfg = dict(secondary_cfg or {})
        self._store = pairing_store

    @property
    def enabled(self) -> bool:
        return bool(self._cfg.get("enabled", False))

    def check(self, platform: str, user_id: str) -> bool:
        """Poll approval state. Fail-closed on any error."""
        return is_secondary_allowed(self._cfg, self._store, platform, user_id)

    def assert_single_provider(self, fallback_chain: list | None) -> None:
        """Assert no fallback chain when single_provider_enforce=true.

        Raises RuntimeError on violation so startup refuses instead of
        silently falling back to another provider.
        """
        if self._cfg.get("single_provider_enforce", False) and (fallback_chain or []):
            raise RuntimeError(
                "secondary.single_provider_enforce=true forbids a fallback chain; "
                "refusing to start instead of silently falling back."
            )
