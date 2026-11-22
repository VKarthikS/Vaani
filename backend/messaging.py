"""Outbound confirmations (WhatsApp first, SMS fallback).

Phase 2 ships a MockMessenger that records messages; Phase 6 adds the Twilio sender
behind the same interface.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, time
from typing import Literal, Protocol

Channel = Literal["whatsapp", "sms"]


class Messenger(Protocol):
    async def send(self, channel: Channel, to: str, body: str) -> bool: ...


@dataclass
class SentMessage:
    channel: Channel
    to: str
    body: str


@dataclass
class MockMessenger:
    """Records messages instead of sending. `fail` lists channels that should fail (tests)."""

    sent: list[SentMessage] = field(default_factory=list)
    fail: set[str] = field(default_factory=set)

    async def send(self, channel: Channel, to: str, body: str) -> bool:
        if channel in self.fail:
            return False
        self.sent.append(SentMessage(channel, to, body))
        return True


def spoken_clock(t: time) -> str:
    """20:30 -> '8:30 PM' (for the WhatsApp card)."""
    h = t.hour % 12 or 12
    return f"{h}:{t.minute:02d} {'AM' if t.hour < 12 else 'PM'}"


def confirmation_text(
    *,
    booking_id: str,
    business_name: str,
    area_name: str,
    d: date,
    t: time,
    base_url: str,
    party_size: int | None = None,
    table_id: str | None = None,
    doctor_line: str | None = None,
    fee_line: str | None = None,
) -> str:
    """WhatsApp card format from docs/WEBSITES.md."""
    when = f"{d.strftime('%a')} {d.day} {d.strftime('%b')} · {spoken_clock(t)}"
    detail = f"{when} · {party_size} people · Table {table_id}" if party_size else when
    lines = ["✅ Booking confirmed — Vaani", f"{business_name}, {area_name}", detail]
    if doctor_line:
        lines.append(doctor_line)
    if fee_line:
        lines.append(fee_line)
    lines += [
        f"Booking ID: {booking_id}",
        f"Status & directions: {base_url.rstrip('/')}/b/{booking_id}",
        "(Sample booking for a hackathon demo)",
    ]
    return "\n".join(lines)
