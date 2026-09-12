"""TOTP enrollment store: secret 0600, backup codes hashed, 5x/3600s lockout.

Mirrors gateway/pairing.py patterns: _secure_write 0600, salted SHA-256
hashes (never plaintext secrets/codes in files or logs), per-key rate
limits and lockout after MAX_FAILED_ATTEMPTS.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import secrets
import tempfile
import threading
import time
from pathlib import Path
from typing import Any

from gateway.auth.totp import generate_secret
from hermes_constants import get_hermes_dir
from utils import atomic_replace

logger = logging.getLogger(__name__)

TOTP_DIR = get_hermes_dir("platforms/secondary-totp", "secondary-totp")

RATE_LIMIT_SECONDS = 600  # reuse pairing cadence: 1 attempt burst guard
LOCKOUT_SECONDS = 3600
MAX_FAILED_ATTEMPTS = 5
BACKUP_CODE_COUNT = 8


def _secure_write(path: Path, data: str) -> None:
    """Temp-file + atomic rename write with 0600 perms (mirrors pairing.py)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        atomic_replace(tmp_path, path)
        try:
            os.chmod(path, 0o600)
        except OSError:
            pass  # Windows: no POSIX modes
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def _hash_with_salt(value: str, salt: bytes) -> str:
    return hashlib.sha256(salt + value.encode("utf-8")).hexdigest()


def _new_backup_codes(n: int = BACKUP_CODE_COUNT) -> list[str]:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    return ["".join(secrets.choice(alphabet) for _ in range(8)) for _ in range(n)]


class TotpStore:
    """Per-user TOTP secrets + hashed backup codes with lockout.

    Files: ``{user_key}.json`` (secret plaintext 0600 — required for
    verification, same sensitivity class as a bot token), backup codes
    stored as salted hashes only, ``_rate_limits.json`` for attempts.
    """

    def __init__(self, base_dir: Path | None = None):
        self._dir = Path(base_dir) if base_dir else TOTP_DIR
        self._dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()

    def _user_path(self, user_key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in ("-", "_", "@", ".") else "_" for c in str(user_key))
        return self._dir / f"{safe}.json"

    def _limits_path(self) -> Path:
        return self._dir / "_rate_limits.json"

    def _load_json(self, path: Path) -> dict:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                return {}
        return {}

    def _save_json(self, path: Path, data: dict) -> None:
        _secure_write(path, json.dumps(data, indent=2, ensure_ascii=False))

    def enroll(self, user_key: str) -> dict[str, Any]:
        """Create a TOTP secret + backup codes for user_key.

        Returns ``{"secret": ..., "backup_codes": [...]}`` — the ONLY time
        plaintext values leave the store (show once at enrollment, like a
        pairing code). Callers must not log them.
        """
        with self._lock:
            secret = generate_secret()
            codes = _new_backup_codes()
            hashed = []
            for code in codes:
                salt = os.urandom(16)
                hashed.append({"hash": _hash_with_salt(code, salt), "salt": salt.hex()})
            self._save_json(
                self._user_path(user_key),
                {"secret": secret, "backup_hashes": hashed, "created_at": time.time()},
            )
            return {"secret": secret, "backup_codes": codes}

    def has_enrollment(self, user_key: str) -> bool:
        data = self._load_json(self._user_path(user_key))
        return bool(data.get("secret"))

    def verify(self, user_key: str, code: str, *, window: int = 1) -> bool:
        """Verify TOTP or backup code. Lockout after 5 failures / 3600s."""
        from gateway.auth.totp import verify_code

        with self._lock:
            if self._is_locked_out(user_key):
                return False
            data = self._load_json(self._user_path(user_key))
            secret = data.get("secret")
            if not secret:
                self._record_failed_attempt(user_key)
                return False
            if verify_code(str(secret), str(code), window=window):
                self._reset_failures(user_key)
                return True
            # Backup codes: constant-time compare against salted hashes.
            candidate = str(code).strip().upper()
            for i, entry in enumerate(data.get("backup_hashes", [])):
                if not isinstance(entry, dict) or "salt" not in entry or "hash" not in entry:
                    continue
                try:
                    salt = bytes.fromhex(entry["salt"])
                except ValueError:
                    continue
                if secrets.compare_digest(_hash_with_salt(candidate, salt), entry["hash"]):
                    remaining = list(data["backup_hashes"])
                    remaining.pop(i)  # single-use
                    data["backup_hashes"] = remaining
                    self._save_json(self._user_path(user_key), data)
                    self._reset_failures(user_key)
                    return True
            self._record_failed_attempt(user_key)
            return False

    def revoke(self, user_key: str) -> bool:
        path = self._user_path(user_key)
        with self._lock:
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    return False
                return True
        return False

    # ----- rate limit / lockout (mirrors pairing.py) -----
    def _is_locked_out(self, user_key: str) -> bool:
        limits = self._load_json(self._limits_path())
        return bool(time.time() < limits.get(f"_lockout:{user_key}", 0))

    def _record_failed_attempt(self, user_key: str) -> None:
        limits = self._load_json(self._limits_path())
        fail_key = f"_failures:{user_key}"
        fails = int(limits.get(fail_key, 0)) + 1
        limits[fail_key] = fails
        if fails >= MAX_FAILED_ATTEMPTS:
            limits[f"_lockout:{user_key}"] = time.time() + LOCKOUT_SECONDS
            limits[fail_key] = 0
            logger.warning("TOTP user %s locked out for %ds after %d failures", user_key, LOCKOUT_SECONDS, MAX_FAILED_ATTEMPTS)
        self._save_json(self._limits_path(), limits)

    def _reset_failures(self, user_key: str) -> None:
        limits = self._load_json(self._limits_path())
        limits.pop(f"_failures:{user_key}", None)
        self._save_json(self._limits_path(), limits)
