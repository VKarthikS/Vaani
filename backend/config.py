"""Backend settings from environment / .env (names: docs/CONTRACTS.md §6)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    supabase_db_url: str = ""
    public_base_url: str = "http://localhost:3000"
    demo_area_1: str = "jubilee_hills"
    demo_area_2: str = "gachibowli"
    dev_simulate: bool = False

    payment_provider: Literal["mock", "razorpay", "stripe"] = "mock"
    payment_key_id: str = ""
    payment_key_secret: str = ""
    payment_webhook_secret: str = ""

    # Per-business partner portal passcodes are derived from this (scripts/partner_passcodes.py).
    partner_passcode_secret: str = "vaani-demo"

    @field_validator("partner_passcode_secret")
    @classmethod
    def _default_when_blank(cls, v: str) -> str:
        return v or "vaani-demo"  # `PARTNER_PASSCODE_SECRET=` in .env means "use the demo default"

    llm_base_url: str = ""
    llm_model: str = ""
    llm_api_key: str = ""

    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""
    twilio_whatsapp_from: str = ""

    data_dir: Path = REPO_ROOT / "data"

    @property
    def demo_areas(self) -> tuple[str, str]:
        return (self.demo_area_1, self.demo_area_2)


@lru_cache
def get_settings() -> Settings:
    return Settings()
