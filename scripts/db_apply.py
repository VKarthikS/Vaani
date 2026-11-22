"""Apply supabase/schema.sql → rls.sql → seed.sql to a Postgres database.

    uv run python scripts/db_apply.py               # all three, SUPABASE_DB_URL from .env
    uv run python scripts/db_apply.py --no-seed     # schema + RLS only
    uv run python scripts/db_apply.py --db-url postgresql://...

Same command for local Supabase (`supabase status` → DB URL) and a hosted project
(Project Settings → Database → connection string). All files are idempotent.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from backend.db import SQL_FILES, SUPABASE_DIR, connect, run_sql  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db-url", help="Postgres URL (default: SUPABASE_DB_URL from .env)")
    ap.add_argument("--no-seed", action="store_true", help="skip seed.sql")
    args = ap.parse_args(argv)

    files = [f for f in SQL_FILES if not (args.no_seed and f == "seed.sql")]
    with connect(args.db_url) as conn:
        for name in files:
            run_sql(conn, (SUPABASE_DIR / name).read_text(encoding="utf-8"))
            print(f"✓ applied {name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
