"""Payment webhook (signature-checked) and the mock test-mode pay action."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter, Request

from backend import payments
from backend.api.deps import Svc, fail

router = APIRouter(prefix="/api/payments")

SIGNATURE_HEADERS = {"mock": "X-Vaani-Signature", "razorpay": "X-Razorpay-Signature"}


@router.post("/webhook")
async def webhook(svc: Svc, request: Request) -> dict[str, Any]:
    """Mock provider payload: {"event": "payment.paid", "payment_id": "...", "provider_ref": "..."},
    signed with HMAC-SHA256(PAYMENT_WEBHOOK_SECRET, raw body) in X-Vaani-Signature."""
    provider = svc.settings.payment_provider
    if provider != "mock":
        fail("NOT_IMPLEMENTED", f"{provider} webhooks arrive in Phase 6", 501)
    if not svc.settings.payment_webhook_secret:
        fail("MISCONFIGURED", "PAYMENT_WEBHOOK_SECRET is not set", 503)
    body = await request.body()  # raw bytes: the signature covers them exactly
    if not payments.verify(svc.settings.payment_webhook_secret, body, request.headers.get(SIGNATURE_HEADERS[provider])):
        fail("BAD_SIGNATURE", "Webhook signature check failed", 401)
    try:
        event = json.loads(body)
    except json.JSONDecodeError:
        fail("INVALID_ARGS", "Body is not JSON")
    if event.get("event") != "payment.paid":
        return {"ok": True, "ignored": event.get("event")}
    try:
        result = await payments.mark_paid(svc.store, str(event.get("payment_id")), event.get("provider_ref"))
    except LookupError as e:
        fail("NOT_FOUND", str(e), 404)
    return {"ok": True, **result}


@router.post("/{booking_id}/mock-pay")
async def mock_pay(svc: Svc, booking_id: str) -> dict[str, Any]:
    """The "Pay (test)" button on /pay/[booking_id]; same path as a paid webhook."""
    if svc.settings.payment_provider != "mock":
        fail("NOT_AVAILABLE", "Mock payments are only on when PAYMENT_PROVIDER=mock", 404)
    b = await svc.store.fetchrow("select * from public.bookings where booking_id = %(b)s", {"b": booking_id})
    if b is None:
        fail("UNKNOWN_BOOKING", f"No booking {booking_id}")
    if b["status"] == "paid":
        fail("ALREADY_PAID", "This booking is already paid")
    if b["status"] != "pending_payment" or not b["amount_due_inr"]:
        fail("NOTHING_TO_PAY", "No deposit or fee is due for this booking")
    pay = await payments.get_or_create_payment(svc.store, booking_id, b["amount_due_inr"], "mock")
    result = await payments.mark_paid(svc.store, pay["payment_id"], provider_ref=f"mock_{pay['payment_id']}")
    return {"ok": True, "amount_inr": pay["amount_inr"], **result}
