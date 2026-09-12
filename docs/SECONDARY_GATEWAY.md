# Secondary Gateway (HONEST-ONLY)

Secondary messaging channel that can **never approve users itself**.
Approval happens only via the **primary channel**:

```bash
hermes pairing approve <platform> <code>
hermes pairing approve-secondary <platform> <code>  # same flow + tier-config check
```

## Tier matrix

| Tier | Capability | TOTP | Notes |
|------|------------|------|-------|
| T1 | Read-only status queries | required | default |
| T2 | T1 + non-destructive lookups | required | tools allowed, no actions |
| T3 | T2 + limited allowlisted actions | required | explicit allowlist |
| T4 | T3 + broader actions | required | operator confirmation path |
| T5 | Full agent capability | required | needs `t5_explicit_opt_in: true` |

Invalid tier, missing `primary_channel`, or T5 without explicit opt-in ->
**refuse-start** (no silent fallback, no auto-correct).

## Commands

```bash
# config.yaml
secondary:
  enabled: false            # default: off
  tier: T1
  primary_channel: telegram # required when enabled
  totp_required: true
  single_provider_enforce: false
totp:
  issuer: hermes-secondary
  window: 1
```

```bash
hermes pairing list
hermes pairing approve-secondary telegram ABCDEFGH
```

## Rollback

Snapshots live under `~/.hermes/secondary/snapshots/` (0600).
Rollback restores a snapshot **only if younger than 30 s**,
otherwise it refuses (won't restore stale config):

```python
from pathlib import Path
from gateway.secondary.audit import take_config_snapshot, rollback_snapshot_if_recent
snap = take_config_snapshot(Path("~/.hermes/config.yaml").expanduser())
rollback_snapshot_if_recent(snap, Path("~/.hermes/config.yaml").expanduser())
```

## Prohibitions (HONEST-ONLY)

- NEVER remove/bypass rate-limit, lockout, or 0600 file permissions.
- NEVER store or log plaintext secrets, backup codes, or TOTP codes.
- NEVER stub validators to `return True` en masse.
- NEVER touch hardline/file-deny/SSRF-metadata guards.
- NEVER fall back silently (fallback chain + `single_provider_enforce` = refuse-start).
- NEVER auto-approve without the primary channel.
- NEVER use model/filter tricks to bypass ToS.
- Origin is `verified` **only** when approved + allow_from + TOTP all hold;
  anything else is `untrusted`.

## External infra limits (honest scope)

- Real TOTP verification needs the `secondary-auth` extra
  (`pyotp==2.9.0`, `qrcode==7.4.2`): `uv pip install 'hermes-agent[secondary-auth]'`.
  Without it, TOTP helpers raise a clear error (fail-closed, no stub pass).
- Unit tests stub `pyotp` deterministically and do **not** cover real-TOTP
  interop (stated in the test module docstring).
- Audit log: local JSONL only; no external SIEM shipper is configured.
