"""Minimal Postgres access for scripts and DB tests (psycopg 3).

The FastAPI backend (Phase 2) gets its own repository layer; this module only knows how
to find the connection string and run SQL files.
"""

from __future__ import annotations

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
SUPABASE_DIR = REPO_ROOT / "supabase"
SQL_FILES = ("schema.sql", "rls.sql", "seed.sql")


def db_url() -> str | None:
    load_dotenv(REPO_ROOT / ".env")
    return os.environ.get("SUPABASE_DB_URL") or None


def connect(url: str | None = None) -> psycopg.Connection:
    """Autocommit connection: each statement (or script) manages its own transaction."""
    url = url or db_url()
    if not url:
        raise SystemExit("SUPABASE_DB_URL is not set (see .env.example; local: `supabase status`).")
    return psycopg.connect(url, autocommit=True)


def run_sql(conn: psycopg.Connection, sql: str) -> None:
    """Run a multi-statement script. With no parameters psycopg sends it as one query,
    so a script's own begin/commit wraps it atomically."""
    conn.execute(sql.encode())  # bytes: arbitrary script text, no placeholders
