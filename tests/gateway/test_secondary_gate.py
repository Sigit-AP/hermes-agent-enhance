"""Tests for gateway/secondary (gate, tiers, origin, audit) — HONEST-ONLY.

No external deps. Uses a fake PairingStore stub; never approves anything.
"""

import json
import sys
import time

import pytest

from gateway.secondary.audit import (
    append_audit_event,
    rollback_snapshot_if_recent,
    take_config_snapshot,
)
from gateway.secondary.gate import SecondaryGate, is_secondary_allowed
from gateway.secondary.origin import tag_origin
from gateway.secondary.tiers import (
    VALID_TIERS,
    get_tier,
    validate_secondary_config,
)


class _FakePairingStore:
    def __init__(self, approved=()):
        self._approved = set(approved)
        self.locked = False

    def is_approved(self, platform, user_id):
        return (platform, user_id) in self._approved

    def _is_locked_out(self, platform):
        return self.locked


@pytest.mark.skipif(
    sys.platform.startswith("win"),
    reason="POSIX file modes are not enforced on Windows",
)
def test_audit_file_is_0600(tmp_path, monkeypatch):
    import gateway.secondary.audit as audit_mod

    monkeypatch.setattr(audit_mod, "AUDIT_DIR", tmp_path)
    monkeypatch.setattr(audit_mod, "AUDIT_FILE", tmp_path / "audit.jsonl")
    target = append_audit_event({"event": "test"})
    mode = oct(target.stat().st_mode & 0o777)
    assert mode == "0o600"
    assert json.loads(target.read_text(encoding="utf-8").strip())["event"] == "test"


def test_audit_never_logs_secrets(tmp_path, monkeypatch):
    import gateway.secondary.audit as audit_mod

    monkeypatch.setattr(audit_mod, "AUDIT_DIR", tmp_path)
    monkeypatch.setattr(audit_mod, "AUDIT_FILE", tmp_path / "audit.jsonl")
    target = append_audit_event({"event": "x", "secret": "ABC", "code": "123", "token": "t"})
    body = target.read_text(encoding="utf-8")
    assert "ABC" not in body
    assert '"secret"' not in body and '"code"' not in body and '"token"' not in body


def test_gate_polls_but_never_approves():
    store = _FakePairingStore(approved={("telegram", "u1")})
    cfg = {"enabled": True, "tier": "T1"}
    assert is_secondary_allowed(cfg, store, "telegram", "u1") is True
    assert is_secondary_allowed(cfg, store, "telegram", "stranger") is False
    # Fail-closed cases
    assert is_secondary_allowed({"enabled": False}, store, "telegram", "u1") is False
    assert is_secondary_allowed(cfg, None, "telegram", "u1") is False
    assert is_secondary_allowed(cfg, store, "", "u1") is False
    assert is_secondary_allowed(cfg, store, "telegram", "") is False
    # No approve method exists on the gate
    assert not hasattr(SecondaryGate(cfg, store), "approve")
    assert not hasattr(SecondaryGate(cfg, store), "approve_code")


def test_gate_fails_closed_on_store_error():
    class _Boom:
        def is_approved(self, platform, user_id):
            raise RuntimeError("db down")

    assert is_secondary_allowed({"enabled": True}, _Boom(), "telegram", "u1") is False


def test_single_provider_enforce_refuses_fallback():
    gate = SecondaryGate({"enabled": True, "single_provider_enforce": True}, _FakePairingStore())
    with pytest.raises(RuntimeError):
        gate.assert_single_provider([{"provider": "x", "model": "y"}])
    gate.assert_single_provider([])  # empty chain is fine


def test_tiers_validate_refuse_start():
    assert validate_secondary_config({"enabled": False}) == []
    assert validate_secondary_config(None) == []
    errs = validate_secondary_config({"enabled": True, "tier": "T9", "primary_channel": "cli"})
    assert any("tier" in e for e in errs)
    errs = validate_secondary_config({"enabled": True, "tier": "T1", "primary_channel": ""})
    assert any("primary_channel" in e for e in errs)
    errs = validate_secondary_config({"enabled": True, "tier": "T5", "primary_channel": "cli"})
    assert any("t5_explicit_opt_in" in e for e in errs)
    ok = validate_secondary_config(
        {"enabled": True, "tier": "T2", "primary_channel": "cli", "totp_required": True}
    )
    assert ok == []
    assert set(VALID_TIERS) == {"T1", "T2", "T3", "T4", "T5"}
    assert get_tier("t3") is not None
    assert get_tier("T9") is None


def test_origin_verified_only_on_full_proof():
    assert tag_origin(approved=True, allow_from=True, totp_ok=True) == "verified"
    assert tag_origin(approved=True, allow_from=True, totp_ok=False) == "untrusted"
    assert tag_origin(approved=True, allow_from=False, totp_ok=True) == "untrusted"
    assert tag_origin(approved=False, allow_from=True, totp_ok=True) == "untrusted"
    assert tag_origin(approved=False, allow_from=False, totp_ok=False) == "untrusted"


def test_snapshot_rollback_window(tmp_path):
    cfg = tmp_path / "config.yaml"
    cfg.write_text("a: 1", encoding="utf-8")
    snap = take_config_snapshot(cfg, snapshot_dir=tmp_path / "snaps")
    cfg.write_text("a: 2", encoding="utf-8")
    assert rollback_snapshot_if_recent(snap, cfg) is True
    assert cfg.read_text(encoding="utf-8") == "a: 1"
    # Stale snapshot refuses
    old = tmp_path / "snaps" / "old.bak"
    old.write_text("a: 0", encoding="utf-8")
    import os

    ancient = time.time() - 3600
    os.utime(old, (ancient, ancient))
    cfg.write_text("a: 2", encoding="utf-8")
    assert rollback_snapshot_if_recent(old, cfg, window_seconds=30) is False
    assert cfg.read_text(encoding="utf-8") == "a: 2"
    # Missing snapshot refuses
    assert rollback_snapshot_if_recent(tmp_path / "nope.bak", cfg) is False
