"""answer_faq, confirmations, payment links, call control and the tool runner."""

from __future__ import annotations

import pytest

from backend.catalog.models import Catalog
from backend.messaging import MockMessenger
from backend.tests.conftest import day
from backend.tools import REGISTRY, ToolContext, run_tool

pytestmark = pytest.mark.db


async def _book_restaurant(ctx: ToolContext, party: int = 2) -> str:
    r = await run_tool(
        ctx,
        "book_table",
        {
            "restaurant_id": "r_jh_01",
            "date": day(1).isoformat(),
            "time": "20:30",
            "party_size": party,
            "name": "Pranav",
        },
    )
    assert r["ok"], r
    return str(r["booking_id"])


async def _book_doctor(ctx: ToolContext) -> str:
    r = await run_tool(
        ctx,
        "book_appointment",
        {"doctor_id": "d_gb_01_derm_1", "date": day(1).isoformat(), "time": "11:00", "name": "Lakshmi"},
    )
    assert r["ok"], r
    return str(r["booking_id"])


# ---------------------------------------------------------------------------
# answer_faq
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("business", "question", "lang", "expect"),
    [
        ("r_jh_01", "parking unda?", "te", "parking"),
        ("r_gb_01", "bachchon ke liye theek hai kya?", "hi", "bachchon"),
        ("h_jh_01", "insurance cashless untunda?", "te", "cashless"),
        ("h_gb_03", "emergency 24 ghante khula hai?", "hi", "24x7"),
        ("r_jh_04", "what are your timings", "en", "open every day"),
        ("r_jh_02", "do I need to pay a deposit for 8 people?", "en", "deposit"),
    ],
)
async def test_answer_faq(ctx: ToolContext, business: str, question: str, lang: str, expect: str) -> None:
    r = await run_tool(ctx, "answer_faq", {"business_id": business, "question": question, "lang": lang})
    assert r["ok"] and r["lang"] == lang and expect.lower() in r["answer"].lower(), r


async def test_answer_faq_unknown(ctx: ToolContext) -> None:
    r = await run_tool(ctx, "answer_faq", {"business_id": "r_jh_01", "question": "is there wifi for my laptop"})
    assert r["ok"] and r["unknown"] is True
    r = await run_tool(ctx, "answer_faq", {"business_id": "r_zz_01", "question": "parking?"})
    assert r["error"] == "UNKNOWN_BUSINESS"


# ---------------------------------------------------------------------------
# send_confirmation / create_payment_link
# ---------------------------------------------------------------------------


async def test_whatsapp_card_format(ctx: ToolContext, messenger: MockMessenger) -> None:
    bid = await _book_restaurant(ctx, 6)
    r = await run_tool(ctx, "send_confirmation", {"booking_id": bid})
    assert r == {"ok": True, "status": "sent", "channel": "whatsapp", "message": messenger.sent[0].body}
    body = messenger.sent[0].body.splitlines()
    assert messenger.sent[0].to == "+919876543210"
    assert body[0] == "✅ Booking confirmed — Vaani"
    assert body[1] == "Spice Garden, Jubilee Hills"
    assert body[2].endswith("· 8:30 PM · 6 people · Table T7")
    assert body[3] == f"Booking ID: {bid}"
    assert body[4] == f"Status & directions: https://vaani.test/b/{bid}"
    assert body[5] == "(Sample booking for a hackathon demo)"


async def test_sms_fallback_and_failure(ctx: ToolContext, messenger: MockMessenger) -> None:
    bid = await _book_restaurant(ctx)
    messenger.fail = {"whatsapp"}
    r = await run_tool(ctx, "send_confirmation", {"booking_id": bid})
    assert r["status"] == "sent" and r["channel"] == "sms"
    messenger.fail = {"whatsapp", "sms"}
    r = await run_tool(ctx, "send_confirmation", {"booking_id": bid})
    assert r["ok"] and r["status"] == "failed"


async def test_hospital_card_has_fee_and_test_pay_link(ctx: ToolContext, messenger: MockMessenger) -> None:
    bid = await _book_doctor(ctx)
    await run_tool(ctx, "send_confirmation", {"booking_id": bid})
    text = messenger.sent[0].body
    assert "Dr. Ananya Rao · Dermatology" in text and f"Fee ₹600 · Pay (test): https://vaani.test/pay/{bid}" in text


async def test_payment_link_reuses_open_payment(ctx: ToolContext) -> None:
    bid = await _book_doctor(ctx)
    a = await run_tool(ctx, "create_payment_link", {"booking_id": bid})
    b = await run_tool(ctx, "create_payment_link", {"booking_id": bid})
    assert a["ok"] and a["mode"] == "test" and a["amount_inr"] == 600 and a["url"].endswith(f"/pay/{bid}")
    assert a["payment_id"] == b["payment_id"]


async def test_payment_link_rules(ctx: ToolContext) -> None:
    bid = await _book_restaurant(ctx, 2)  # no deposit for 2 people
    r = await run_tool(ctx, "create_payment_link", {"booking_id": bid})
    assert r["error"] == "NOTHING_TO_PAY"
    r = await run_tool(ctx, "create_payment_link", {"booking_id": "VN-0000"})
    assert r["error"] == "UNKNOWN_BOOKING"


# ---------------------------------------------------------------------------
# control tools + runner
# ---------------------------------------------------------------------------


async def test_control_tools(ctx: ToolContext) -> None:
    r = await run_tool(ctx, "switch_service", {"to": "hospital", "reason": "caller asked for a doctor"})
    assert r == {"ok": True, "service": "hospital"}
    assert (await run_tool(ctx, "transfer_to_human", {"reason": "asked for a person"}))["callback_requested"] is True
    assert (await run_tool(ctx, "end_call", {}))["end"] is True
    assert ctx.call_id
    types = [e["type"] for e in await ctx.store.events(ctx.call_id)]
    assert types == ["agent_switched", "tool_called", "tool_called", "tool_called"]


async def test_runner_contract(ctx: ToolContext, catalog: Catalog) -> None:
    assert set(REGISTRY) == {
        "resolve_area",
        "search_restaurants",
        "get_restaurant_slots",
        "book_table",
        "map_speciality",
        "search_hospitals",
        "get_doctor_slots",
        "book_appointment",
        "answer_faq",
        "send_confirmation",
        "create_payment_link",
        "switch_service",
        "transfer_to_human",
        "end_call",
    }
    r = await run_tool(ctx, "make_coffee", {})
    assert r["error"] == "UNKNOWN_TOOL"
    r = await run_tool(ctx, "resolve_area", {"text": "Jubilee Hills", "surprise": 1})
    assert r["error"] == "INVALID_ARGS"
    entry = ctx.timeline[-1]
    assert set(entry) == {"ts", "tool", "args", "result", "summary", "ms"} and entry["ms"] >= 0
    assert ctx.call_id
    events = await ctx.store.events(ctx.call_id)
    assert events and all(
        set(e["payload"]) == {"tool", "summary", "ms", "ok"} for e in events if e["type"] == "tool_called"
    )


async def test_runner_without_call_writes_no_events(ctx: ToolContext) -> None:
    call_id, ctx.call_id = ctx.call_id, None
    await run_tool(ctx, "resolve_area", {"text": "Gachibowli"})
    assert call_id and await ctx.store.events(call_id) == []
    assert ctx.timeline[-1]["tool"] == "resolve_area"
