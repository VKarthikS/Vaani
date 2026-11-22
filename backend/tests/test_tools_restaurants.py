"""resolve_area + restaurant tools against the seeded placeholder data."""

from __future__ import annotations

import asyncio
from datetime import datetime, time
from typing import Any

import pytest

from backend import clock
from backend.tests.conftest import day
from backend.tools import ToolContext, run_tool

pytestmark = pytest.mark.db


async def tool_events(ctx: ToolContext) -> list[dict[str, Any]]:
    assert ctx.call_id
    return [e for e in await ctx.store.events(ctx.call_id) if e["type"] == "tool_called"]


# ---------------------------------------------------------------------------
# resolve_area
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "area"),
    [
        ("Jubilee Hills lo manchi restaurant cheppu", "jubilee_hills"),
        ("gachibouli mein", "gachibowli"),
        ("జూబ్లీ హిల్స్", "jubilee_hills"),
        ("jubli hils", "jubilee_hills"),
        ("near Gachibowli", "gachibowli"),
        ("JH", "jubilee_hills"),
    ],
)
async def test_resolve_area_supported(ctx: ToolContext, text: str, area: str) -> None:
    r = await run_tool(ctx, "resolve_area", {"text": text})
    assert r["ok"] and r["area_id"] == area


@pytest.mark.parametrize(
    ("text", "heard"),
    [("Kukatpally lo", "Kukatpally"), ("Secunderabad", "Secunderabad"), ("Banjara Hills", "Banjara Hills")],
)
async def test_resolve_area_unsupported(ctx: ToolContext, text: str, heard: str) -> None:
    r = await run_tool(ctx, "resolve_area", {"text": text})
    assert r["ok"] and r["unsupported"] is True and r["heard"] == heard
    assert set(r["supported"]) == {"jubilee_hills", "gachibowli"}
    assert set(r["reply"]) == {"te", "hi", "en"} and "Gachibowli" in r["reply"]["en"]


# ---------------------------------------------------------------------------
# search_restaurants
# ---------------------------------------------------------------------------


async def test_search_top3_by_rating_matches_demo_script(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx, "search_restaurants", {"area_id": "jubilee_hills", "party_size": 6, "date": day(1).isoformat()}
    )
    assert r["ok"]
    names = [x["name"] for x in r["results"]]
    assert names == ["Spice Garden", "Coastal Kitchen", "Green Leaf"]  # CALL_FLOW.md Hindi sample
    ratings = [x["rating"] for x in r["results"]]
    assert ratings == sorted(ratings, reverse=True)
    events = await tool_events(ctx)
    assert events[-1]["payload"]["summary"].startswith(
        "Searched restaurants → 3 matches in Jubilee Hills (6 people, tomorrow"
    )


async def test_search_never_returns_more_than_three(ctx: ToolContext) -> None:
    for area in ("jubilee_hills", "gachibowli"):
        r = await run_tool(ctx, "search_restaurants", {"area_id": area, "party_size": 2, "date": day(2).isoformat()})
        assert len(r["results"]) <= 3


async def test_search_with_time_skips_full_restaurants(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx,
        "search_restaurants",
        {"area_id": "jubilee_hills", "party_size": 2, "date": day(1).isoformat(), "time": "20:00"},
    )
    assert "r_jh_01" not in [x["restaurant_id"] for x in r["results"]]  # Spice Garden is full at 20:00


async def test_search_filters(ctx: ToolContext) -> None:
    veg = await run_tool(
        ctx,
        "search_restaurants",
        {"area_id": "jubilee_hills", "party_size": 2, "date": day(1).isoformat(), "food_type": "veg"},
    )
    assert all(x["food_type"] in ("veg", "both") for x in veg["results"])
    biryani = await run_tool(
        ctx,
        "search_restaurants",
        {"area_id": "gachibowli", "party_size": 4, "date": day(1).isoformat(), "cuisine": "biryani"},
    )
    assert [x["restaurant_id"] for x in biryani["results"]] == ["r_gb_03"]  # via its popular dishes


async def test_search_rules(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx, "search_restaurants", {"area_id": "kukatpally", "party_size": 2, "date": day(1).isoformat()}
    )
    assert r == {
        "ok": False,
        "error": "UNSUPPORTED_AREA",
        "message": "kukatpally is not a demo area",
        "supported": ["jubilee_hills", "gachibowli"],
    }
    r = await run_tool(
        ctx, "search_restaurants", {"area_id": "jubilee_hills", "party_size": 20, "date": day(1).isoformat()}
    )
    assert r["ok"] and r["results"] == [] and r["reason"] == "party_too_large"
    r = await run_tool(
        ctx, "search_restaurants", {"area_id": "jubilee_hills", "party_size": 2, "date": day(9).isoformat()}
    )
    assert r["error"] == "DATE_OUT_OF_RANGE"


# ---------------------------------------------------------------------------
# get_restaurant_slots
# ---------------------------------------------------------------------------


async def test_slot_full_offers_two_nearest(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx,
        "get_restaurant_slots",
        {"restaurant_id": "r_jh_01", "date": day(1).isoformat(), "party_size": 6, "time": "20:00"},
    )
    assert r["requested_full"] is True and r["nearest"] == ["19:30", "20:30"]
    assert "20:00" not in r["free"]
    events = await tool_events(ctx)
    assert events[-1]["payload"]["summary"] == "Checked Spice Garden slots → 20:00 full, offered 19:30, 20:30"


async def test_slots_respect_blocks_and_party_limit(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx, "get_restaurant_slots", {"restaurant_id": "r_jh_02", "date": day(2).isoformat(), "party_size": 2}
    )
    assert "13:00" not in r["free"]  # staff-blocked in the seed
    r = await run_tool(
        ctx, "get_restaurant_slots", {"restaurant_id": "r_jh_05", "date": day(2).isoformat(), "party_size": 9}
    )
    assert r["error"] == "PARTY_TOO_LARGE" and r["max_party_size"] == 8


async def test_slots_today_hide_past_times(ctx: ToolContext, monkeypatch: pytest.MonkeyPatch) -> None:
    fake_now = datetime.combine(day(0), time(20, 10), clock.IST)
    monkeypatch.setattr(clock, "now_ist", lambda: fake_now)
    r = await run_tool(
        ctx, "get_restaurant_slots", {"restaurant_id": "r_gb_01", "date": day(0).isoformat(), "party_size": 2}
    )
    assert r["ok"] and all(t > "20:10" for t in r["free"])


# ---------------------------------------------------------------------------
# book_table
# ---------------------------------------------------------------------------


async def test_book_table_happy_path_emits_events(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx,
        "book_table",
        {"restaurant_id": "r_jh_01", "date": day(1).isoformat(), "time": "20:30", "party_size": 6, "name": "Pranav"},
    )
    assert r["ok"] and r["booking_id"].startswith("VN-") and r["deposit_needed"] is False
    assert ctx.call_id
    types = [e["type"] for e in await ctx.store.events(ctx.call_id)]
    assert types == ["booking_created", "tool_called"]
    row = await ctx.store.fetchrow(
        "select phone, call_id, language, source from public.bookings where booking_id = %(b)s", {"b": r["booking_id"]}
    )
    assert row == {"phone": "+919876543210", "call_id": ctx.call_id, "language": "hi", "source": "vaani_call"}
    assert ctx.timeline[-1]["tool"] == "book_table" and ctx.timeline[-1]["summary"].startswith("Booked table T")


async def test_book_table_deposit(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx,
        "book_table",
        {"restaurant_id": "r_jh_01", "date": day(3).isoformat(), "time": "20:30", "party_size": 10, "name": "Rohit"},
    )
    assert r["deposit_needed"] is True and r["deposit_inr"] == 500


@pytest.mark.parametrize(
    ("args", "code"),
    [
        ({"restaurant_id": "r_jh_01", "date": 1, "time": "20:00", "party_size": 2}, "SLOT_FULL"),
        ({"restaurant_id": "r_jh_02", "date": 2, "time": "13:00", "party_size": 2}, "BLOCKED"),
        ({"restaurant_id": "r_jh_05", "date": 2, "time": "20:00", "party_size": 9}, "PARTY_TOO_LARGE"),
        ({"restaurant_id": "r_jh_01", "date": 1, "time": "17:00", "party_size": 2}, "INVALID_TIME"),
        ({"restaurant_id": "r_zz_01", "date": 1, "time": "20:00", "party_size": 2}, "UNKNOWN_BUSINESS"),
        ({"restaurant_id": "r_jh_01", "date": 1, "time": "20:00", "party_size": 0}, "INVALID_ARGS"),
        ({"restaurant_id": "r_jh_01", "date": 1, "time": "8:30pm", "party_size": 2}, "INVALID_ARGS"),
    ],
)
async def test_book_table_rules(ctx: ToolContext, args: dict[str, object], code: str) -> None:
    args = {**args, "date": day(int(args["date"])).isoformat(), "name": "Test"}  # type: ignore[call-overload]
    r = await run_tool(ctx, "book_table", args)
    assert r["ok"] is False and r["error"] == code


async def test_book_table_needs_caller_phone(ctx: ToolContext) -> None:
    ctx.phone = None
    r = await run_tool(
        ctx,
        "book_table",
        {"restaurant_id": "r_jh_01", "date": day(1).isoformat(), "time": "20:30", "party_size": 2, "name": "X"},
    )
    assert r["error"] == "MISSING_DETAILS"


async def test_double_booking_race_through_tools(ctx: ToolContext) -> None:
    """10 concurrent tool calls for the only 12-seat table at Spice Garden → exactly one wins."""
    args = {"restaurant_id": "r_jh_01", "date": day(3).isoformat(), "time": "20:30", "party_size": 11, "name": "Racer"}
    results = await asyncio.gather(*(run_tool(ctx, "book_table", dict(args)) for _ in range(10)))
    assert sum(r["ok"] for r in results) == 1
    assert {r.get("error") for r in results if not r["ok"]} == {"SLOT_FULL"}
