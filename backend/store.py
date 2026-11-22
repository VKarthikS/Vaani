"""Async Postgres access for the backend (psycopg 3 pool).

The backend talks to Supabase Postgres directly (SUPABASE_DB_URL) rather than through the
REST API: lower latency on every voice turn and real transactions. Realtime still fires
because it watches the database itself. Live state (slots, leave, bookings, payments,
calls, events) is read from here; catalogue text comes from data/ (backend.catalog).
"""

from __future__ import annotations

import uuid
from typing import Any, LiteralString

from psycopg import AsyncConnection
from psycopg.rows import DictRow, dict_row
from psycopg.types.json import Jsonb
from psycopg_pool import AsyncConnectionPool

Row = dict[str, Any]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


class Store:
    def __init__(self, url: str, min_size: int = 1, max_size: int = 10) -> None:
        self.pool: AsyncConnectionPool[AsyncConnection[DictRow]] = AsyncConnectionPool(
            url,
            min_size=min_size,
            max_size=max_size,
            open=False,
            kwargs={"autocommit": True, "row_factory": dict_row},
            connection_class=AsyncConnection[DictRow],
        )

    async def open(self) -> None:
        await self.pool.open(wait=True, timeout=10)

    async def close(self) -> None:
        await self.pool.close()

    # -- generic helpers ---------------------------------------------------

    async def fetch(self, query: LiteralString, params: dict[str, Any] | None = None) -> list[Row]:
        async with self.pool.connection() as conn:
            cur = await conn.execute(query, params)
            return list(await cur.fetchall())

    async def fetchrow(self, query: LiteralString, params: dict[str, Any] | None = None) -> Row | None:
        async with self.pool.connection() as conn:
            cur = await conn.execute(query, params)
            return await cur.fetchone()

    async def execute(self, query: LiteralString, params: dict[str, Any] | None = None) -> int:
        async with self.pool.connection() as conn:
            cur = await conn.execute(query, params)
            return cur.rowcount

    # -- calls and events ----------------------------------------------------

    async def start_call(self, channel: str, from_number: str | None, direction: str = "inbound") -> str:
        call_id = new_id("c")
        await self.execute(
            "insert into public.calls (call_id, channel, direction, from_number)"
            " values (%(id)s, %(ch)s, %(dir)s, %(from)s)",
            {"id": call_id, "ch": channel, "dir": direction, "from": from_number},
        )
        return call_id

    async def emit(self, call_id: str, type_: str, payload: dict[str, Any]) -> None:
        """Insert a call_events row; Supabase Realtime pushes it to the Studio/portals."""
        await self.execute(
            "insert into public.call_events (call_id, type, payload) values (%(c)s, %(t)s, %(p)s)",
            {"c": call_id, "t": type_, "p": Jsonb(payload)},
        )

    async def events(self, call_id: str) -> list[Row]:
        return await self.fetch(
            "select type, payload, ts from public.call_events where call_id = %(c)s order by id", {"c": call_id}
        )
