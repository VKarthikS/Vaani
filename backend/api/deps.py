"""Shared app services and FastAPI dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, NoReturn

from fastapi import Depends, Header, HTTPException, Request

from backend import partners
from backend.catalog.models import Catalog
from backend.config import Settings
from backend.messaging import Messenger
from backend.store import Store
from backend.tools.base import ToolContext, ToolError


@dataclass
class Services:
    settings: Settings
    store: Store
    catalog: Catalog
    messenger: Messenger

    def tool_context(self, **kw: Any) -> ToolContext:
        return ToolContext(
            store=self.store, catalog=self.catalog, settings=self.settings, messenger=self.messenger, **kw
        )

    def business_ids(self) -> set[str]:
        return {r.restaurant_id for r in self.catalog.restaurants} | {h.hospital_id for h in self.catalog.hospitals}


def services(request: Request) -> Services:
    svc: Services = request.app.state.services
    return svc


Svc = Annotated[Services, Depends(services)]
PasscodeHeader = Annotated[str | None, Header(alias="X-Partner-Passcode")]

# ToolError code → HTTP status
STATUS = {
    "UNKNOWN_BUSINESS": 404,
    "UNKNOWN_DOCTOR": 404,
    "UNKNOWN_BOOKING": 404,
    "NOT_FOUND": 404,
    "SLOT_FULL": 409,
    "SLOT_TAKEN": 409,
    "BLOCKED": 409,
    "ALREADY_PAID": 409,
    "INVALID_TRANSITION": 409,
    "FORBIDDEN": 403,
}


def fail(code: str, message: str, status: int | None = None) -> NoReturn:
    raise HTTPException(status_code=status or STATUS.get(code, 400), detail={"error": code, "message": message})


def fail_tool(e: ToolError) -> NoReturn:
    fail(e.code, e.message)


def require_partner(svc: Services, business_id: str, given: str | None) -> None:
    if business_id not in svc.business_ids():
        fail("UNKNOWN_BUSINESS", f"No business {business_id}")
    if not partners.check(svc.settings.partner_passcode_secret, business_id, given):
        fail("FORBIDDEN", "Wrong or missing partner passcode (X-Partner-Passcode)")
