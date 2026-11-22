"""send_confirmation and create_payment_link."""

from __future__ import annotations

from typing import Any, Literal

from backend.messaging import confirmation_text
from backend.payments import get_or_create_payment
from backend.tools.base import Args, Result, ToolContext, ToolError, tool


async def load_booking(ctx: ToolContext, booking_id: str) -> dict[str, Any]:
    row = await ctx.store.fetchrow("select * from public.bookings where booking_id = %(b)s", {"b": booking_id})
    if row is None:
        raise ToolError("UNKNOWN_BOOKING", f"No booking {booking_id}")
    return row


def booking_message(ctx: ToolContext, b: dict[str, Any], pay_url: str | None = None) -> str:
    areas = {a.area_id: a.name_en for a in ctx.catalog.areas}
    base = ctx.settings.public_base_url
    if b["service"] == "restaurant":
        r = next(x for x in ctx.catalog.restaurants if x.restaurant_id == b["business_id"])
        fee = f"Deposit ₹{b['amount_due_inr']} · Pay (test): {pay_url}" if pay_url and b["amount_due_inr"] else None
        return confirmation_text(
            booking_id=b["booking_id"],
            business_name=r.name,
            area_name=areas[r.area_id],
            d=b["date"],
            t=b["time"],
            base_url=base,
            party_size=b["party_size"],
            table_id=b["table_id"],
            fee_line=fee,
        )
    h = next(x for x in ctx.catalog.hospitals if x.hospital_id == b["business_id"])
    d = next(x for x in ctx.catalog.doctors if x.doctor_id == b["doctor_id"])
    fee = (
        f"Fee ₹{b['amount_due_inr']}" + (f" · Pay (test): {pay_url}" if pay_url else "")
        if b["amount_due_inr"]
        else None
    )
    return confirmation_text(
        booking_id=b["booking_id"],
        business_name=h.name,
        area_name=areas[h.area_id],
        d=b["date"],
        t=b["time"],
        base_url=base,
        doctor_line=f"{d.name} · {d.speciality}",
        fee_line=fee,
    )


class CreatePaymentLinkArgs(Args):
    booking_id: str


@tool("create_payment_link", CreatePaymentLinkArgs, "Test-mode payment link for a deposit or consultation fee.")
async def create_payment_link(ctx: ToolContext, a: CreatePaymentLinkArgs) -> tuple[Result, str]:
    b = await load_booking(ctx, a.booking_id)
    if b["status"] == "paid":
        raise ToolError("ALREADY_PAID", "This booking is already paid")
    if b["status"] != "pending_payment" or not b["amount_due_inr"]:
        raise ToolError("NOTHING_TO_PAY", "No deposit or fee is due for this booking")
    pay = await get_or_create_payment(ctx.store, b["booking_id"], b["amount_due_inr"], ctx.settings.payment_provider)
    # Mock provider: our own /pay page. Razorpay/Stripe hosted links arrive in Phase 6.
    url = f"{ctx.settings.public_base_url.rstrip('/')}/pay/{b['booking_id']}"
    return (
        {"url": url, "amount_inr": pay["amount_inr"], "payment_id": pay["payment_id"], "mode": "test"},
        f"Payment link (test) · ₹{pay['amount_inr']} · {b['booking_id']}",
    )


class SendConfirmationArgs(Args):
    booking_id: str
    channel: Literal["whatsapp", "sms"] = "whatsapp"


@tool(
    "send_confirmation", SendConfirmationArgs, "Send the booking card to the caller's number (WhatsApp, SMS fallback)."
)
async def send_confirmation(ctx: ToolContext, a: SendConfirmationArgs) -> tuple[Result, str]:
    b = await load_booking(ctx, a.booking_id)
    pay_url = None
    if b["status"] == "pending_payment" and b["amount_due_inr"]:
        # Include the test-mode pay link in the card (direct call: not a separate timeline entry).
        link, _ = await create_payment_link(ctx, CreatePaymentLinkArgs(booking_id=b["booking_id"]))
        pay_url = link["url"]
    body = booking_message(ctx, b, pay_url)
    order: list[Literal["whatsapp", "sms"]] = [a.channel] + (["sms"] if a.channel == "whatsapp" else [])
    for ch in order:
        if await ctx.messenger.send(ch, b["phone"], body):
            label = "WhatsApp" if ch == "whatsapp" else "SMS"
            return {"status": "sent", "channel": ch, "message": body}, f"{label} confirmation sent · {b['booking_id']}"
    return {
        "status": "failed",
        "channel": a.channel,
    }, f"Confirmation failed on {' and '.join(order)} · {b['booking_id']}"
