"""POST /api/dev/simulate-booking — a fake call that books through the real tools, so the
websites see exactly the events a phone call produces. Only when DEV_SIMULATE=true."""

from __future__ import annotations

import datetime as dt
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from backend.api.deps import Svc, fail
from backend.clock import today_ist
from backend.text import mask_phone
from backend.tools import run_tool

router = APIRouter(prefix="/api/dev")

SIM_PHONE = "+910000000000"


class SimulateBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    business_id: str
    doctor_id: str | None = None
    date: dt.date | None = None
    time: dt.time | None = None
    party_size: int = Field(default=2, ge=1, le=50)
    name: str = "Demo Guest"
    language: Literal["te", "hi", "en"] = "hi"


@router.post("/simulate-booking")
async def simulate_booking(svc: Svc, body: SimulateBody) -> dict[str, Any]:
    if not svc.settings.dev_simulate:
        fail("NOT_FOUND", "Not found", 404)
    is_rest = body.business_id in {r.restaurant_id for r in svc.catalog.restaurants}
    hosp = next((h for h in svc.catalog.hospitals if h.hospital_id == body.business_id), None)
    if not is_rest and hosp is None:
        fail("UNKNOWN_BUSINESS", f"No business {body.business_id}")

    call_id = await svc.store.start_call("web", SIM_PHONE)
    ctx = svc.tool_context(call_id=call_id, phone=SIM_PHONE, language=body.language)
    await svc.store.emit(
        call_id, "call_started", {"channel": "web", "from_masked": mask_phone(SIM_PHONE), "simulated": True}
    )
    await svc.store.emit(call_id, "language_detected", {"lang": body.language, "confidence": 1.0, "via": "simulated"})
    await svc.store.emit(call_id, "agent_switched", {"from": "router", "to": "restaurant" if is_rest else "hospital"})

    d = body.date or today_ist()
    if is_rest:
        slots = await run_tool(
            ctx,
            "get_restaurant_slots",
            {"restaurant_id": body.business_id, "date": d.isoformat(), "party_size": body.party_size},
        )
        time = _pick(slots, body.time)
        booked = await run_tool(
            ctx,
            "book_table",
            {
                "restaurant_id": body.business_id,
                "date": d.isoformat(),
                "time": time,
                "party_size": body.party_size,
                "name": body.name,
            },
        )
    else:
        assert hosp is not None
        doctor_id = body.doctor_id or next(
            x.doctor_id for x in svc.catalog.doctors if x.hospital_id == hosp.hospital_id
        )
        slots = await run_tool(ctx, "get_doctor_slots", {"doctor_id": doctor_id, "date": d.isoformat()})
        time = _pick(slots, body.time)
        booked = await run_tool(
            ctx, "book_appointment", {"doctor_id": doctor_id, "date": d.isoformat(), "time": time, "name": body.name}
        )

    if not booked["ok"]:
        await svc.store.emit(call_id, "call_ended", {"outcome": "no_availability", "duration_s": 0})
        fail(booked["error"], booked["message"])
    sent = await run_tool(ctx, "send_confirmation", {"booking_id": booked["booking_id"]})
    await svc.store.emit(
        call_id, "call_ended", {"outcome": "booked", "duration_s": 0, "booking_id": booked["booking_id"]}
    )
    await svc.store.execute(
        "update public.calls set ended_at = now(), summary = 'Simulated booking' where call_id = %(c)s", {"c": call_id}
    )
    return {"call_id": call_id, "booking": booked, "confirmation": sent, "timeline": ctx.timeline}


def _pick(slots: dict[str, Any], wanted: dt.time | None) -> str:
    if not slots.get("ok"):
        fail(slots.get("error", "NO_SLOTS"), slots.get("message", "No slots"))
    free: list[str] = slots.get("free", [])
    if wanted is not None:
        return wanted.strftime("%H:%M")  # let the booking tool enforce the rules
    if not free:
        fail("NO_AVAILABILITY", "No free slot on that date", 409)
    return free[0]
