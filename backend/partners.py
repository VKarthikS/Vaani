"""Per-business demo passcodes for the partner portals (a known limit: not real auth).

passcode = first 6 digits of HMAC-SHA256(PARTNER_PASSCODE_SECRET, business_id).
`uv run python scripts/partner_passcodes.py` prints the list for the team.
"""

from __future__ import annotations

import hashlib
import hmac


def passcode(secret: str, business_id: str) -> str:
    digest = hmac.new(secret.encode(), business_id.encode(), hashlib.sha256).hexdigest()
    return f"{int(digest, 16) % 1_000_000:06d}"


def check(secret: str, business_id: str, given: str | None) -> bool:
    return bool(given) and hmac.compare_digest(passcode(secret, business_id), (given or "").strip())
