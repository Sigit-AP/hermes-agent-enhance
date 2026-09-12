"""Tests for gateway/auth TOTP store — HONEST-ONLY.

NOTE: pyotp/qrcode are NOT installed in this environment (verified via
``python -c "import pyotp"`` -> ModuleNotFoundError). These tests therefore
inject a deterministic fake ``pyotp`` module into ``sys.modules`` so they
verify TotpStore logic (enroll/verify/backup-single-use/lockout/0600)
without the real extra. Real-TOTP integration requires installing
``hermes-agent[secondary-auth]``; that path is NOT covered here and is
not claimed as tested.
"""

import sys
import types

import pytest

# --- Deterministic fake pyotp (injected before gateway.auth.totp import) ---
_FAKE_SECRET = "JBSWY3DPEHPK3PXP"


class _FakeTOTP:
    def __init__(self, secret):
        self.secret = secret

    def verify(self, code, valid_window=1, for_time=None):
        if not self.secret:
            raise ValueError("empty secret")  # mirrors real pyotp: caught -> False
        return str(code).strip() == "123456"

    def now(self):
        return "123456"

    def at(self, for_time):
        return "123456"

    def provisioning_uri(self, name=None, issuer_name=None):
        return f"otpauth://totp/{issuer_name}:{name}?secret={self.secret}&issuer={issuer_name}"


_fake_pyotp = types.ModuleType("pyotp")
_fake_pyotp.random_base32 = lambda: _FAKE_SECRET
_fake_pyotp.TOTP = _FakeTOTP
_fake_totp_mod = types.ModuleType("pyotp.totp")
_fake_totp_mod.TOTP = _FakeTOTP
_fake_pyotp.totp = _fake_totp_mod
sys.modules.setdefault("pyotp", _fake_pyotp)
sys.modules.setdefault("pyotp.totp", _fake_totp_mod)

from gateway.auth.totp import (  # noqa: E402
    current_code_for_test,
    generate_secret,
    provisioning_uri,
    verify_code,
)
from gateway.auth.totp_store import TotpStore  # noqa: E402


def _make_store(tmp_path):
    return TotpStore(base_dir=tmp_path)


def test_generate_and_verify_roundtrip():
    secret = generate_secret()
    assert secret == _FAKE_SECRET
    assert verify_code(secret, "123456") is True
    assert verify_code(secret, "000000") is False
    assert verify_code("", "123456") is False  # fail-closed, no crash


def test_provisioning_uri_shape():
    uri = provisioning_uri(_FAKE_SECRET, account="alice", issuer="hermes-secondary")
    assert uri.startswith("otpauth://totp/")
    assert _FAKE_SECRET not in uri or "secret=" in uri  # secret stays in URI (QR enrollment)
    assert "hermes-secondary" in uri


def test_current_code_helper():
    assert current_code_for_test(_FAKE_SECRET) == "123456"


def test_enroll_verify_backup_single_use(tmp_path):
    store = _make_store(tmp_path)
    enrolled = store.enroll("alice")
    assert enrolled["secret"] == _FAKE_SECRET
    assert len(enrolled["backup_codes"]) == 8
    assert store.has_enrollment("alice") is True
    # TOTP path
    assert store.verify("alice", "123456") is True
    # Backup code path: single-use
    backup = enrolled["backup_codes"][0]
    assert backup != "123456"
    assert store.verify("alice", backup) is True
    assert store.verify("alice", backup) is False  # consumed
    # Secrets never persisted in plaintext for backup codes
    raw = (tmp_path / "alice.json").read_text(encoding="utf-8")
    assert backup not in raw


def test_lockout_after_five_failures(tmp_path):
    store = _make_store(tmp_path)
    store.enroll("bob")
    for _ in range(5):
        assert store.verify("bob", "wrong-code") is False
    # Locked out: even the right code now fails (fail-closed)
    assert store.verify("bob", "123456") is False
    # Unknown user fails closed too
    assert store.verify("nobody", "123456") is False


def test_revoke(tmp_path):
    store = _make_store(tmp_path)
    store.enroll("carol")
    assert store.revoke("carol") is True
    assert store.has_enrollment("carol") is False
    assert store.revoke("carol") is False


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="POSIX file modes are not enforced on Windows",
)
def test_store_file_is_0600(tmp_path):
    store = _make_store(tmp_path)
    store.enroll("dave")
    mode = oct((tmp_path / "dave.json").stat().st_mode & 0o777)
    assert mode == "0o600"
