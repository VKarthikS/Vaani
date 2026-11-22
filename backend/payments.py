"""Test-mode payments: links, webhook signature check, and marking a booking paid.

Phase 2 implements the `mock` provider end to end (mock /pay page + signed webhook).
Razorpay / Stripe adapters plug in behind the same functions in Phase 6.
"""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from psycopg.rows import dict_row

from backend.store import Row, Store, new_id


def sign(secret: str, body: bytes) -> str:
    """HMAC-SHA256 hex digest — the same scheme Razorpay uses for X-Razorpay-Signature."""
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def verify(secret: str, body: bytes, signature: str | None) -> bool:
    if not secret or not signature:
        return False
    return hmac.compare_digest(sign(secret, body), signature.strip())


async def get_or_create_payment(store: Store, booking_id: str, amount_inr: int, provider: str) -> Row:
    """One open payment per booking; creating a link twice reuses it."""
    existing = await store.fetchrow(
        "select * from public.payments where booking_id = %(b)s and status = 'created' order by created_at limit 1",
        {"b": booking_id},
    )
    if existing:
        return existing
    row = await store.fetchrow(
        "insert into public.payments (payment_id, booking_id, amount_inr, provider)"
        " values (%(p)s, %(b)s, %(a)s, %(pr)s)"
        " returning *",
        {"p": new_id("pay"), "b": booking_id, "a": amount_inr, "pr": provider},
    )
    assert row is not None
    return row


async def mark_paid(store: Store, payment_id: str, provider_ref: str | None = None) -> dict[str, Any]:
    """Payment → paid, booking pending_payment → paid, in one transaction. Idempotent.
    Emits payment_updated when the booking came from a call."""
    async with store.pool.connection() as conn, conn.transaction():
        cur = conn.cursor(row_factory=dict_row)
        await cur.execute("select * from public.payments where payment_id = %(p)s for update", {"p": payment_id})
        pay = await cur.fetchone()
        if pay is None:
            raise LookupError(f"No payment {payment_id}")
        already = pay["status"] == "paid"
        if not already:
            await cur.execute(
                "update public.payments set status = 'paid', provider_ref = coalesce(%(ref)s, provider_ref)"
                " where payment_id = %(p)s",
                {"p": payment_id, "ref": provider_ref},
            )
            await cur.execute(
                "update public.bookings set status = 'paid' where booking_id = %(b)s and status = 'pending_payment'",
                {"b": pay["booking_id"]},
            )
        await cur.execute(
            "select booking_id, status, call_id from public.bookings where booking_id = %(b)s", {"b": pay["booking_id"]}
        )
        booking = await cur.fetchone()
    assert booking is not None
    if not already and booking["call_id"]:
        await store.emit(
            booking["call_id"],
            "payment_updated",
            {"booking_id": booking["booking_id"], "payment_id": payment_id, "status": "paid"},
        )
    return {
        "payment_id": payment_id,
        "booking_id": booking["booking_id"],
        "booking_status": booking["status"],
        "already_paid": already,
    }
