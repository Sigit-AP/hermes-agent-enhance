"""TOTP helpers with lazy pyotp import (HONEST-ONLY, no plaintext logs)."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)


def _load_pyotp():
    try:
        from tools.lazy_deps import ensure as _ensure

        _ensure("auth.secondary", prompt=False)
    except Exception:
        pass
    try:
        import pyotp  # type: ignore

        return pyotp
    except ImportError as exc:
        raise RuntimeError(
            "TOTP requires the 'secondary-auth' extra "
            "(pyotp==2.9.0, qrcode==7.4.2). Install with: "
            "uv pip install 'hermes-agent[secondary-auth]'"
        ) from exc


def generate_secret() -> str:
    """Generate a new base32 TOTP secret (never logged by callers)."""
    pyotp = _load_pyotp()
    return str(pyotp.random_base32())


def verify_code(secret: str, code: str, *, window: int = 1, for_time: float | None = None) -> bool:
    """Verify a TOTP code. Fail-closed on any error. No secret in logs."""
    try:
        pyotp = _load_pyotp()
        totp = pyotp.TOTP(str(secret))
        kwargs: dict = {"valid_window": int(window)}
        if for_time is not None:
            kwargs["for_time"] = for_time
        return bool(totp.verify(str(code).strip(), **kwargs))
    except Exception as exc:
        logger.warning("TOTP verify failed (fail-closed): %s", type(exc).__name__)
        return False


def provisioning_uri(secret: str, *, account: str, issuer: str) -> str:
    """Build the otpauth:// URI for QR enrollment."""
    pyotp = _load_pyotp()
    return str(pyotp.totp.TOTP(str(secret)).provisioning_uri(name=account, issuer_name=issuer))


def current_code_for_test(secret: str, *, for_time: float | None = None) -> str:
    """Return current TOTP code. Test helper only — never log the result."""
    pyotp = _load_pyotp()
    totp = pyotp.TOTP(str(secret))
    if for_time is not None:
        return str(totp.at(int(for_time)))
    return str(totp.now())
