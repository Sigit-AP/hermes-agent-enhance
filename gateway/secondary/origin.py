"""Origin tagging: verified only on full proof, else untrusted."""

from __future__ import annotations

from typing import Literal

OriginTag = Literal["verified", "untrusted"]


def tag_origin(*, approved: bool, allow_from: bool, totp_ok: bool) -> OriginTag:
    """Tag a secondary message origin.

    ``verified`` requires ALL of: PairingStore approval + allow_from match +
    TOTP success. Anything else -> ``untrusted``. No silent fallback.
    """
    if bool(approved) and bool(allow_from) and bool(totp_ok):
        return "verified"
    return "untrusted"
