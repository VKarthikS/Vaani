"""map_speciality + hospital tools."""

from __future__ import annotations

import pytest

from backend.catalog.models import Catalog
from backend.tests.conftest import day
from backend.tools import ToolContext, run_tool

pytestmark = pytest.mark.db


# ---------------------------------------------------------------------------
# map_speciality
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "spec"),
    [
        ("skin doctor kavali", "Dermatology"),
        ("pillala doctor chudandi", "Pediatrics"),
        ("दांत दर्द है", "Dental"),
        ("aankh ka doctor chahiye", "Ophthalmology"),
        ("I need a dermatolojist", "Dermatology"),  # mis-heard
        ("heart doctor please", "Cardiology"),  # not an emergency
        ("ENT specialist", "ENT"),
        ("Gachibowli lo gynecologist kavali", "Gynecology"),
    ],
)
async def test_map_speciality(ctx: ToolContext, text: str, spec: str) -> None:
    r = await run_tool(ctx, "map_speciality", {"text": text})
    assert r["ok"] and r.get("speciality") == spec and "emergency" not in r


async def test_knee_pain_is_not_chest_pain(ctx: ToolContext) -> None:
    """Regression: these share 'ने में दर्द' and used to fuzzy-match as an emergency."""
    r = await run_tool(ctx, "map_speciality", {"text": "घुटने में दर्द"})
    assert r.get("speciality") == "Orthopedics" and "emergency" not in r


@pytest.mark.parametrize(
    ("text", "lang"),
    [
        ("Naanna ki gunde noppi, chaathi lo baruvuga undi", "te"),
        ("meri maa behosh ho gayi hain", "hi"),
        ("my friend had a road accident, heavy bleeding", "en"),
        ("my father has chest pane", "en"),  # one letter off
        ("सीने में दर्द हो रहा है", "hi"),
    ],
)
async def test_emergency_detected_first(ctx: ToolContext, text: str, lang: str) -> None:
    r = await run_tool(ctx, "map_speciality", {"text": text, "lang": lang})
    assert r["emergency"] is True and "108" in r["reply"] and "112" in r["reply"]
    assert r["reply"] == getattr(ctx.catalog.speciality_mapping.emergency_reply, lang)


async def test_every_data_phrase_maps(ctx: ToolContext, catalog: Catalog) -> None:
    m = catalog.speciality_mapping
    for p in m.phrases:
        r = await run_tool(ctx, "map_speciality", {"text": p.phrase})
        assert r.get("speciality") == p.speciality, p.phrase
    for e in m.emergency_phrases:
        r = await run_tool(ctx, "map_speciality", {"text": e.phrase})
        assert r.get("emergency") is True, e.phrase


async def test_unknown_need(ctx: ToolContext) -> None:
    r = await run_tool(ctx, "map_speciality", {"text": "my car broke down"})
    assert r["ok"] and r["unknown"] is True


# ---------------------------------------------------------------------------
# search_hospitals / get_doctor_slots
# ---------------------------------------------------------------------------


async def test_search_hospitals_top3_by_rating(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx, "search_hospitals", {"area_id": "gachibowli", "speciality": "Dermatology", "date": day(1).isoformat()}
    )
    assert [x["hospital_id"] for x in r["results"]] == ["h_gb_01", "h_gb_02", "h_gb_05"]
    first = r["results"][0]
    assert first["doctor_id"] == "d_gb_01_derm_1" and first["fee_inr"] == 600 and first["window"] == "10:00-13:00"
    assert first["next_free"]["date"] >= day(1).isoformat()


async def test_search_hospitals_skips_leave_day(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx, "search_hospitals", {"area_id": "gachibowli", "speciality": "General Medicine", "date": day(2).isoformat()}
    )
    udayam = next(x for x in r["results"] if x["hospital_id"] == "h_gb_02")
    assert udayam["next_free"]["date"] == day(3).isoformat()  # Dr. Priya Reddy is on leave on +2


async def test_search_hospitals_rules(ctx: ToolContext) -> None:
    r = await run_tool(ctx, "search_hospitals", {"area_id": "jubilee_hills", "speciality": "Dental"})
    assert [x["hospital_id"] for x in r["results"]] == ["h_jh_05"]
    r = await run_tool(ctx, "search_hospitals", {"area_id": "jubilee_hills", "speciality": "Astrology"})
    assert r["error"] == "INVALID_ARGS"
    r = await run_tool(ctx, "search_hospitals", {"area_id": "kondapur", "speciality": "ENT"})
    assert r["error"] == "UNSUPPORTED_AREA"


async def test_doctor_fully_booked_points_to_next_day(ctx: ToolContext) -> None:
    r = await run_tool(ctx, "get_doctor_slots", {"doctor_id": "d_jh_02_derm_1", "date": day(1).isoformat()})
    assert r["free"] == [] and r["fully_booked"] is True and r["next_free_date"] == day(2).isoformat()


async def test_doctor_on_leave_and_blocked(ctx: ToolContext) -> None:
    r = await run_tool(ctx, "get_doctor_slots", {"doctor_id": "d_gb_02_genmed_1", "date": day(2).isoformat()})
    assert r["on_leave"] is True and r["free"] == [] and r["fully_booked"] is False
    r = await run_tool(ctx, "get_doctor_slots", {"doctor_id": "d_gb_01_cardio_1", "date": day(1).isoformat()})
    status = await ctx.store.fetchrow(
        "select status from public.doctor_slots where doctor_id = 'd_gb_01_cardio_1' and date = %(d)s and time = '10:00'",
        {"d": day(1)},
    )
    assert status == {"status": "blocked"} and "10:00" not in r["free"] and r["free"]


# ---------------------------------------------------------------------------
# book_appointment
# ---------------------------------------------------------------------------


async def test_book_appointment(ctx: ToolContext) -> None:
    r = await run_tool(
        ctx,
        "book_appointment",
        {"doctor_id": "d_gb_01_derm_1", "date": day(1).isoformat(), "time": "11:00", "name": "Lakshmi"},
    )
    assert r["ok"] and r["fee_inr"] == 600 and r["hospital_id"] == "h_gb_01"
    assert ctx.call_id
    created = [e for e in await ctx.store.events(ctx.call_id) if e["type"] == "booking_created"]
    assert created[0]["payload"]["doctor_id"] == "d_gb_01_derm_1"
    again = await run_tool(
        ctx,
        "book_appointment",
        {"doctor_id": "d_gb_01_derm_1", "date": day(1).isoformat(), "time": "11:00", "name": "X"},
    )
    assert again["error"] == "SLOT_TAKEN"


@pytest.mark.parametrize(
    ("doctor", "offset", "t", "code"),
    [
        ("d_gb_02_genmed_1", 2, "11:00", "DOCTOR_ON_LEAVE"),
        ("d_gb_01_cardio_1", 1, "10:00", "BLOCKED"),
        ("d_jh_02_derm_1", 1, "10:00", "SLOT_TAKEN"),
        ("d_gb_01_derm_1", 1, "15:00", "INVALID_TIME"),
        ("d_zz_01_derm_1", 1, "10:00", "UNKNOWN_DOCTOR"),
    ],
)
async def test_book_appointment_rules(ctx: ToolContext, doctor: str, offset: int, t: str, code: str) -> None:
    r = await run_tool(
        ctx, "book_appointment", {"doctor_id": doctor, "date": day(offset).isoformat(), "time": t, "name": "X"}
    )
    assert r["error"] == code
