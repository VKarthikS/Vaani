"""Print the demo partner-portal passcode for every business.

    uv run python scripts/partner_passcodes.py

Passcodes are derived from PARTNER_PASSCODE_SECRET (backend/partners.py), so changing the
secret in .env changes them all. Demo-grade access control only (docs/LIMITS.md).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.catalog.loader import load_catalog  # noqa: E402
from backend.config import get_settings  # noqa: E402
from backend.partners import passcode  # noqa: E402


def main() -> int:
    settings = get_settings()
    cat = load_catalog(settings.data_dir)
    rows = [(r.restaurant_id, r.name, f"/partner/r/{r.slug}") for r in cat.restaurants]
    rows += [(h.hospital_id, h.name, f"/partner/h/{h.slug}") for h in cat.hospitals]
    width = max(len(n) for _, n, _ in rows)
    for business_id, name, path in rows:
        print(f"{passcode(settings.partner_passcode_secret, business_id)}  {business_id:8}  {name:<{width}}  {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
