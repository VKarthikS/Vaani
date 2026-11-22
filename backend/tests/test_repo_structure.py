"""Phase 0 guard rails: the repo layout and env contract stay in sync with the docs."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED_PATHS = [
    "docs/MASTER_PLAN.md",
    "docs/ARCHITECTURE.md",
    "docs/CONTRACTS.md",
    "docs/CALL_FLOW.md",
    "docs/WEBSITES.md",
    "docs/DEMO.md",
    "docs/DATA_PROMPT.md",
    "docs/TEAM.md",
    "docs/LIMITS.md",
    "frontend",
    "backend/voice",
    "backend/flows/prompts/te",
    "backend/flows/prompts/hi",
    "backend/flows/prompts/en",
    "backend/tools",
    "backend/postcall",
    "backend/api",
    "backend/eval/recordings",
    "backend/tests",
    "data",
    "scripts",
    "supabase",
    "docker-compose.yml",
    "CLAUDE.md",
    "README.md",
    "LICENSE",
    "ATTRIBUTIONS.md",
    "AI_USAGE.md",
    "EVAL.md",
    ".env.example",
    ".gitignore",
]


def test_required_paths_exist() -> None:
    missing = [p for p in REQUIRED_PATHS if not (ROOT / p).exists()]
    assert not missing, f"missing: {missing}"


def _env_example_keys() -> set[str]:
    text = (ROOT / ".env.example").read_text()
    return set(re.findall(r"^([A-Z][A-Z0-9_]*)=", text, flags=re.M))


def _contract_env_keys() -> set[str]:
    """Env var names listed in the first column of CONTRACTS.md §6."""
    text = (ROOT / "docs/CONTRACTS.md").read_text()
    section = text.split("## 6. Environment variables", 1)[1].split("\n## ", 1)[0]
    keys: set[str] = set()
    for line in section.splitlines():
        if line.startswith("| ") and not line.startswith("| Variable") and "---" not in line:
            keys.update(re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", line.split("|")[1]))
    return keys


def test_env_example_matches_contract() -> None:
    assert _env_example_keys() == _contract_env_keys()


def test_env_example_has_no_values_for_secrets() -> None:
    text = (ROOT / ".env.example").read_text()
    for key in ("TOKEN", "SECRET", "_KEY"):
        for line in text.splitlines():
            if key in line.split("=", 1)[0] and "=" in line and not line.startswith("#"):
                assert line.split("=", 1)[1].strip() == "", f"secret has a value: {line}"


def test_real_env_is_gitignored() -> None:
    ignore = (ROOT / ".gitignore").read_text().splitlines()
    assert ".env" in ignore and "!.env.example" in ignore
