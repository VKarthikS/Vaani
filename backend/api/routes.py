"""REST endpoints for the websites (docs/CONTRACTS.md §3)."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

import psycopg
from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from backend.api.deps import PasscodeHeader, Svc, fail, require_partner
from backend.clock import in_window, is_past
from backend.text import mask_phone

router = APIRouter(prefix="/api")


def _hhmm(t: dt.time) -> str:
    return t.strftime("%H:%M")


def public_booking(row: dict[str, Any]) -> dict[str, Any]:
    out = {k: v for k, v in row.items() if k != "phone"}
    out["phone_masked"] = mask_phone(row.get("phone"))
    out["date"] = row["date"].isoformat()
    out["time"] = _hhmm(row["time"])
    return out


# ---------------------------------------------------------------------------
# Public reads
# ---------------------------------------------------------------------------


@router.get("/businesses")
async def businesses(
    svc: Svc, area: str | None = None, type: Literal["restaurant", "hospital"] | None = None
) -> list[dict[str, Any]]:  # noqa: A002
    out: list[dict[str, Any]] = []
    if type in (None, "restaurant"):
        out += [
            {"type": "restaurant", "id": r.restaurant_id, **r.model_dump(exclude={"phone"})}
            for r in svc.catalog.restaurants
            if area in (None, r.area_id)
        ]
    if type in (None, "hospital"):
        for h in svc.catalog.hospitals:
            if area in (None, h.area_id):
                docs = [d.model_dump() for d in svc.catalog.doctors if d.hospital_id == h.hospital_id]
                out.append(
                    {"type": "hospital", "id": h.hospital_id, **h.model_dump(exclude={"phone"}), "doctors": docs}
                )
    return out


@router.get("/restaurants/{restaurant_id}/slots")
async def restaurant_slots(svc: Svc, restaurant_id: str, date: dt.date) -> dict[str, Any]:
    if restaurant_id not in {r.restaurant_id for r in svc.catalog.restaurants}:
        fail("UNKNOWN_BUSINESS", f"No restaurant {restaurant_id}")
    rows = await svc.store.fetch(
        """select s.time, s.blocked, cardinality(s.booked_table_ids) as booked,
                  (select count(*) from public.restaurant_tables t where t.restaurant_id = s.restaurant_id) as total
             from public.restaurant_slots s where s.restaurant_id = %(r)s and s.date = %(d)s order by s.time""",
        {"r": restaurant_id, "d": date},
    )
    slots = [
        {
            "time": _hhmm(r["time"]),
            "free_tables": 0 if r["blocked"] else r["total"] - r["booked"],
            "total_tables": r["total"],
            "blocked": r["blocked"],
            "past": is_past(date, r["time"]),
        }
        for r in rows
    ]
    return {"restaurant_id": restaurant_id, "date": date.isoformat(), "in_window": in_window(date), "slots": slots}


@router.get("/doctors/{doctor_id}/slots")
async def doctor_slots(svc: Svc, doctor_id: str, date: dt.date) -> dict[str, Any]:
    doc = await svc.store.fetchrow(
        "select on_leave_dates from public.doctors where doctor_id = %(d)s", {"d": doctor_id}
    )
    if doc is None:
        fail("UNKNOWN_DOCTOR", f"No doctor {doctor_id}")
    rows = await svc.store.fetch(
        "select time, status from public.doctor_slots where doctor_id = %(d)s and date = %(dt)s order by time",
        {"d": doctor_id, "dt": date},
    )
    return {
        "doctor_id": doctor_id,
        "date": date.isoformat(),
        "on_leave": date in (doc["on_leave_dates"] or []),
        "slots": [{"time": _hhmm(r["time"]), "status": r["status"], "past": is_past(date, r["time"])} for r in rows],
    }


@router.get("/bookings/{booking_id}")
async def get_booking(svc: Svc, booking_id: str) -> dict[str, Any]:
    row = await svc.store.fetchrow("select * from public.bookings where booking_id = %(b)s", {"b": booking_id})
    if row is None:
        fail("UNKNOWN_BOOKING", f"No booking {booking_id}")
    pays = await svc.store.fetch(
        "select payment_id, amount_inr, provider, status, created_at, updated_at from public.payments"
        " where booking_id = %(b)s order by created_at",
        {"b": booking_id},
    )
    return {**public_booking(row), "payments": pays}


# ---------------------------------------------------------------------------
# Partner portals (demo passcode in X-Partner-Passcode)
# ---------------------------------------------------------------------------


@router.get("/partners/{business_id}/bookings")
async def partner_bookings(
    svc: Svc, business_id: str, passcode: PasscodeHeader = None, date: dt.date | None = None
) -> list[dict[str, Any]]:
    require_partner(svc, business_id, passcode)
    rows = await svc.store.fetch(
        """select b.*, (select p.status from public.payments p where p.booking_id = b.booking_id
                         order by p.created_at desc limit 1) as payment_status
             from public.bookings b
            where b.business_id = %(id)s and (%(d)s::date is null or b.date = %(d)s)
            order by b.date, b.time, b.table_id""",
        {"id": business_id, "d": date},
    )
    return [public_booking(r) for r in rows]


class BookingPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    status: Literal["arrived", "checked_in", "cancelled"]


@router.patch("/bookings/{booking_id}")
async def patch_booking(
    svc: Svc, booking_id: str, body: BookingPatch, passcode: PasscodeHeader = None
) -> dict[str, Any]:
    row = await svc.store.fetchrow("select * from public.bookings where booking_id = %(b)s", {"b": booking_id})
    if row is None:
        fail("UNKNOWN_BOOKING", f"No booking {booking_id}")
    if body.status == "cancelled":
        # Callers cancel from the status page without a passcode (demo limit, see LIMITS.md).
        try:
            updated = await svc.store.fetchrow("select * from public.cancel_booking(%(b)s)", {"b": booking_id})
        except psycopg.errors.RaiseException as e:
            fail(str(e.diag.message_primary), str(e.diag.message_hint))
        assert updated is not None
        return public_booking(updated)

    require_partner(svc, row["business_id"], passcode)
    if row["status"] == "cancelled":
        fail("INVALID_TRANSITION", "Booking is cancelled")
    if (body.status == "arrived") != (row["service"] == "restaurant"):
        fail("INVALID_TRANSITION", "Restaurants mark 'arrived'; hospitals mark 'checked_in'")
    updated = await svc.store.fetchrow(
        "update public.bookings set status = %(s)s where booking_id = %(b)s returning *",
        {"s": body.status, "b": booking_id},
    )
    assert updated is not None
    return public_booking(updated)


class BlockBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    business_id: str
    doctor_id: str | None = None
    date: dt.date
    time: dt.time | None = None
    all_day: bool = False
    blocked: bool = True


@router.post("/slots/block")
async def block_slots(svc: Svc, body: BlockBody, passcode: PasscodeHeader = None) -> dict[str, Any]:
    require_partner(svc, body.business_id, passcode)
    if body.time is None and not body.all_day:
        fail("INVALID_ARGS", "Give a time, or all_day: true")
    t = None if body.all_day else body.time
    if body.business_id.startswith("r_"):
        n = await svc.store.execute(
            "update public.restaurant_slots set blocked = %(bl)s"
            " where restaurant_id = %(r)s and date = %(d)s and (%(t)s::time is null or time = %(t)s)",
            {"bl": body.blocked, "r": body.business_id, "d": body.date, "t": t},
        )
    else:
        doc = next((d for d in svc.catalog.doctors if d.doctor_id == body.doctor_id), None)
        if doc is None or doc.hospital_id != body.business_id:
            fail("UNKNOWN_DOCTOR", f"{body.doctor_id} is not a doctor at {body.business_id}")
        # Never touch booked slots: blocking only stops new bookings.
        n = await svc.store.execute(
            "update public.doctor_slots set status = %(st)s"
            " where doctor_id = %(doc)s and date = %(d)s and (%(t)s::time is null or time = %(t)s)"
            " and status <> 'booked'",
            {"st": "blocked" if body.blocked else "free", "doc": doc.doctor_id, "d": body.date, "t": t},
        )
    if n == 0:
        fail("NOT_FOUND", "No matching slot (or only booked slots)")
    return {"ok": True, "updated": n}


class LeaveBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: dt.date
    on_leave: bool = True


@router.post("/doctors/{doctor_id}/leave")
async def doctor_leave(svc: Svc, doctor_id: str, body: LeaveBody, passcode: PasscodeHeader = None) -> dict[str, Any]:
    doc = next((d for d in svc.catalog.doctors if d.doctor_id == doctor_id), None)
    if doc is None:
        fail("UNKNOWN_DOCTOR", f"No doctor {doctor_id}")
    require_partner(svc, doc.hospital_id, passcode)
    row = await svc.store.fetchrow(
        """update public.doctors
              set on_leave_dates = case when %(on)s
                    then (select array_agg(distinct x order by x)
                            from unnest(array_append(on_leave_dates, %(d)s::date)) x)
                    else array_remove(on_leave_dates, %(d)s::date) end
            where doctor_id = %(doc)s returning on_leave_dates""",
        {"on": body.on_leave, "d": body.date, "doc": doctor_id},
    )
    assert row is not None
    return {"ok": True, "on_leave_dates": [d.isoformat() for d in row["on_leave_dates"]]}
