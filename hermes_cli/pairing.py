"""
CLI commands for the DM pairing system.

Usage:
    hermes pairing list              # Show all pending + approved users
    hermes pairing approve <platform> <code>  # Approve a pairing code
    hermes pairing revoke <platform> <user_id> # Revoke user access
    hermes pairing clear-pending     # Clear all expired/pending codes
"""

def pairing_command(args):
    """Handle hermes pairing subcommands."""
    from gateway.pairing import PairingStore

    store = PairingStore()
    action = getattr(args, "pairing_action", None)

    if action == "list":
        _cmd_list(store)
    elif action == "approve":
        _cmd_approve(store, args.platform, args.code)
    elif action == "approve-secondary":
        _cmd_approve_secondary(store, args.platform, args.code)
    elif action == "revoke":
        _cmd_revoke(store, args.platform, args.user_id)
    elif action == "clear-pending":
        _cmd_clear_pending(store)
    else:
        print("Usage: hermes pairing {list|approve|approve-secondary|revoke|clear-pending}")
        print("Run 'hermes pairing --help' for details.")


def _cmd_list(store):
    """List all pending and approved users."""
    pending = store.list_pending()
    approved = store.list_approved()

    if not pending and not approved:
        print("No pairing data found. No one has tried to pair yet~")
        return

    if pending:
        print(f"\n  Pending Pairing Requests ({len(pending)}):")
        print(f"  {'Platform':<12} {'Code':<10} {'User ID':<20} {'Name':<20} {'Age'}")
        print(f"  {'--------':<12} {'----':<10} {'-------':<20} {'----':<20} {'---'}")
        for p in pending:
            print(
                f"  {p['platform']:<12} {p['code']:<10} {p['user_id']:<20} "
                f"{(p.get('user_name') or ''):<20} {p['age_minutes']}m ago"
            )
    else:
        print("\n  No pending pairing requests.")

    if approved:
        print(f"\n  Approved Users ({len(approved)}):")
        print(f"  {'Platform':<12} {'User ID':<20} {'Name':<20}")
        print(f"  {'--------':<12} {'-------':<20} {'----':<20}")
        for a in approved:
            print(f"  {a['platform']:<12} {a['user_id']:<20} {(a.get('user_name') or ''):<20}")
    else:
        print("\n  No approved users.")

    print()


def _cmd_approve(store, platform: str, code: str):
    """Approve a pairing code."""
    platform = platform.lower().strip()
    code = code.upper().strip()

    result = store.approve_code(platform, code)
    if result:
        uid = result["user_id"]
        name = result.get("user_name") or ""
        display = f"{name} ({uid})" if name else uid
        print(f"\n  Approved! User {display} on {platform} can now use the bot~")
        print("  They'll be recognized automatically on their next message.\n")
    elif store._is_locked_out(platform):
        # Disambiguate: approve_code returns None for both invalid codes
        # and lockout. Tell the operator it's lockout so they don't chase
        # a "wrong code" rabbit hole (#10195).
        import time as _time
        limits = store._load_json(store._rate_limit_path())
        lockout_until = limits.get(f"_lockout:{platform}", 0)
        remaining = max(0, int(lockout_until - _time.time()))
        mins = remaining // 60
        print(
            f"\n  Platform '{platform}' is locked out after too many failed "
            f"approval attempts."
        )
        print(f"  Lockout clears in ~{mins} minute(s).")
        print(
            "  To reset sooner, delete the '_lockout:{0}' entry from "
            "~/.hermes/platforms/pairing/_rate_limits.json\n".format(platform)
        )
    else:
        print(f"\n  Code '{code}' not found or expired for platform '{platform}'.")
        print("  Run 'hermes pairing list' to see pending codes.\n")


def _cmd_revoke(store, platform: str, user_id: str):
    """Revoke a user's access."""
    platform = platform.lower().strip()

    if store.revoke(platform, user_id):
        print(f"\n  Revoked access for user {user_id} on {platform}.\n")
    else:
        print(f"\n  User {user_id} not found in approved list for {platform}.\n")


def _cmd_clear_pending(store):
    """Clear all pending pairing codes."""
    count = store.clear_pending()
    if count:
        print(f"\n  Cleared {count} pending pairing request(s).\n")
    else:
        print("\n  No pending requests to clear.\n")


def _cmd_approve_secondary(store, platform: str, code: str):
    """Approve a secondary-channel pairing code via the primary channel.

    Wrapper around the standard approval flow: the secondary channel never
    approves itself — the operator runs this on the primary channel.
    Refuses to approve when the secondary tier config is invalid.
    """
    from gateway.secondary.tiers import validate_secondary_config

    secondary_cfg: dict = {}
    try:
        from gateway.config import load_gateway_config

        cfg = load_gateway_config()
        secondary = getattr(cfg, "secondary", None)
        if isinstance(secondary, dict):
            secondary_cfg = dict(secondary)
        elif secondary is not None and hasattr(secondary, "to_dict"):
            secondary_cfg = dict(secondary.to_dict())
    except Exception:
        secondary_cfg = {}
    errors = validate_secondary_config({**secondary_cfg, "enabled": True})
    if errors:
        print("\n  Refusing secondary approval: invalid secondary config:")
        for err in errors:
            print(f"    - {err}")
        print()
        return
    _cmd_approve(store, platform, code)
