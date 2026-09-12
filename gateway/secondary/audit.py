"""Secondary audit log: JSONL with 0600 perms + 30s snapshot rollback."""

from __future__ import annotations

import json
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from typing import Any

from hermes_constants import get_hermes_dir
from utils import atomic_replace

logger = logging.getLogger(__name__)

AUDIT_DIR = get_hermes_dir("platforms/secondary", "secondary")
AUDIT_FILE = AUDIT_DIR / "audit.jsonl"
SNAPSHOT_ROLLBACK_WINDOW_SECONDS = 30


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


def _redact(event: dict[str, Any]) -> dict[str, Any]:
    """Strip secret-bearing keys so audit logs never carry secrets."""
    redacted = dict(event)
    for key in ("secret", "totp_secret", "backup_code", "code", "token"):
        redacted.pop(key, None)
    return redacted


def append_audit_event(event: dict[str, Any], *, audit_file: Path | None = None) -> Path:
    """Append one JSONL audit event. Never logs secrets. Returns file path."""
    target = Path(audit_file) if audit_file else AUDIT_FILE
    target.parent.mkdir(parents=True, exist_ok=True)
    record = {"ts": time.time(), **_redact(event)}
    line = json.dumps(record, ensure_ascii=False)
    # Append atomically-ish: open in append mode, then enforce 0600.
    with open(target, "a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        try:
            os.fsync(f.fileno())
        except OSError:
            pass
    try:
        os.chmod(target, 0o600)
    except OSError:
        pass
    return target


def take_config_snapshot(config_path: Path, *, snapshot_dir: Path | None = None) -> Path:
    """Copy config file to a timestamped snapshot. Returns snapshot path."""
    src = Path(config_path)
    dest_dir = Path(snapshot_dir) if snapshot_dir else AUDIT_DIR / "snapshots"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"config-{int(time.time() * 1000)}.bak"
    shutil.copy2(src, dest)
    try:
        os.chmod(dest, 0o600)
    except OSError:
        pass
    return dest


def rollback_snapshot_if_recent(
    snapshot: Path,
    config_path: Path,
    *,
    window_seconds: int = SNAPSHOT_ROLLBACK_WINDOW_SECONDS,
    now: float | None = None,
) -> bool:
    """Restore snapshot over config_path if snapshot is within window.

    Returns True when rolled back, False when snapshot is too old (refuses
    stale rollback) or files are missing. Never deletes the live config
    without a valid snapshot source.
    """
    snap = Path(snapshot)
    dest = Path(config_path)
    if not snap.exists() or not snap.is_file():
        logger.warning("Secondary rollback refused: snapshot missing: %s", snap)
        return False
    current = now if now is not None else time.time()
    try:
        age = current - snap.stat().st_mtime
    except OSError:
        return False
    if age > window_seconds:
        logger.warning("Secondary rollback refused: snapshot too old (%.1fs > %ds)", age, window_seconds)
        return False
    try:
        data = snap.read_bytes()
    except OSError:
        return False
    _secure_write(dest, data.decode("utf-8", errors="strict"))
    logger.info("Secondary config rolled back from %s", snap)
    return True
