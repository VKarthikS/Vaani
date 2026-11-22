# Vaani — work log

Every agent session adds an entry here (rules and template: `AGENTS.md` §5). **Newest first.** Read the latest entry before you start. Times are IST; past phases use their commit times (`git log`).

## Current state (keep this short and up to date)

| Phase | Status | Owner | Where |
|---|---|---|---|
| 0 Repo + docs | ✅ done | Pranav | `main` @ `d33536a` |
| 1 Data + database | ✅ done (local Supabase check pending — Docker Desktop wasn't starting) | Pranav | `main` @ `9a2f0b8` |
| 2 Tools + API | ✅ done | Pranav | `main` @ `7343662` |
| 3 Text-mode agent + eval | 🟡 started, handed off (see entry below) | open — Rithvik or Pranav | `main` (WIP modules) |
| 4 Voice over browser | ⬜ not started | open | — |
| 5 Websites | 🟡 in progress outside this repo | Akshit, Karthik | `docs/FRONTEND_PROMPT.md` |
| 6 Phone calls + WhatsApp | ⬜ not started (needs Twilio) | open | — |
| 7 Integration, eval, deploy | ⬜ not started | open | — |
| 8 Submission polish | ⬜ not started | open | — |

Baseline on `main`: `uv run pytest -q` → **131 passed** · ruff ✓ · mypy ✓ · `validate_data.py` ✓ (0 warnings).

## Entries

### 2026-11-22 16:05 IST · Phase 5 · Karthik via Codex · done
**Branch:** `feat/vaani-landing-rebuild`
**Goal:** Rebuild the public landing page for review.
**Done:** rebuilt `/` as an editorial landing page with a custom waveform, English/Telugu/Hindi content, responsive menu and a scripted restaurant or appointment transcript.
**Files:** new Next.js app under `frontend/` and one Playwright landing spec.
**Tests / checks:** lint, typecheck and production build passed. Playwright passed at 1440, 1024 and 390 px. Backend baseline: data validation clean, 31 tests passed and 100 skipped, Ruff and mypy passed.
**Decisions:** original typography layout and waveform. Uses a phone link only when a valid demo number is configured.
**Next steps:** review the landing page before starting other routes or integrating browser calling.

### 2026-11-22 13:04 IST · Phase 3 · Pranav via Claude Code · handed off
**Branch:** `main` · **Commits:** the commit that adds this entry
**Goal:** text-mode agent (router + restaurant + hospital flows), CLI and `eval.py`.
**Done (WIP, unit-checked by hand but no tests yet):**
- `backend/voice/llm.py`: OpenAI-compatible adapter using a **JSON action protocol**. The model replies with one object `{"say": "...", "actions": [{"tool": "...", "args": {...}}]}`; tolerant parser `parse_reply`; `OpenAICompatLLM` (retries 5xx/429, `response_format=json_object`); `ScriptedLLM` test double; `from_env()`.
- `backend/flows/language.py`: `detect_language(text) -> (te|hi|en, confidence)` from script + romanised function words.
- `backend/flows/when.py`: `parse_day(text, today)` (aaj/kal/parso, ivala/repu/ellundi, "3 din baad", "naalugu rojula tarvata", weekdays in en/hi/te, ISO) and `parse_time(text, kind)` ("saadhe aath", "enimidinnara", "okati gantaki", "raat 9 baje", "7:30 pm"; ambiguous hours resolved per restaurant/hospital hours).
- `backend/devdb.py`: throwaway Postgres cluster + seeded **template database** + `clone()` for one fresh DB per eval call (no Docker needed).
- `backend/config.py`: `llm_base_url`, `llm_model`, `llm_api_key` settings. `openai` dependency added.
**Known bug to fix first:** `parse_time` returns `None` for plain clock times: `"8:30"`, `"10:15"`, `"7:30 pm"`, `"saayantram 4:30"`, `"12 noon"`. Cause: `norm()` turns `:` into a space before the `HH:MM` regex runs. Parse times on the raw lower-cased text, not `norm()`'s output, then add unit tests for every case in the Phase 3 prompt.
**LLM findings (Featherless, request-pricing plan, ~$20 credit, concurrency 100):**
- Key lives only in `.env` as `LLM_API_KEY` (git-ignored). Never commit it. `LLM_BASE_URL=https://api.featherless.ai/v1`, `LLM_MODEL=Qwen/Qwen3-30B-A3B-Instruct-2507`.
- **Native tool calling is broken there today**: Qwen3-30B-A3B-Instruct-2507 and Qwen3-14B return HTTP 500 when `tools` is sent; Qwen3-32B ignored the tool, took 19 s and invented restaurants; Qwen3-8B was at capacity. Hence the JSON protocol above.
- JSON mode on Qwen3-30B-A3B-Instruct-2507: valid JSON 3/3, ~1.0–1.6 s warm (3.7 s cold), ~180 prompt tokens for a tiny prompt. Price ≈ $0.125 / 1M input, $0.45 / 1M output, so a full eval run should cost well under $1.
**Tests / checks:** `uv run pytest -q` → 131 passed (no new tests yet) · ruff ✓ · mypy ✓.
**Decisions:** own runner that mirrors Pipecat Flows (`NodeConfig`-like nodes with role/task messages and functions whose handlers return `(result, next_node)`), so Phase 4 wraps the same nodes in a Pipecat `FlowManager` instead of rewriting them. Deterministic guards before the LLM: emergency → 108/112 without calling the LLM, OTP/card mention → refusal line, booking only via `propose_booking` (read-back) then `confirm_booking` on a later turn.
**Blockers / needs:** none for Phase 3 (LLM key present). Local Supabase still unverified (Docker).
**Next steps:** follow "Phase 3" in `docs/PHASE_PROMPTS.md`. It lists the remaining steps in order: fix `parse_time`, context + nodes + guards + session runner, prompts per language, CLI, eval, tests, docs.

### 2026-11-22 12:54 IST · Phase 2 · Pranav via Claude Code · done
**Branch:** `main` · **Commits:** `7343662`, `0771d00`
**Done:** all 14 tools (`backend/tools/`, one runner `run_tool` with Pydantic args, coded errors, tool timeline, `tool_called` events); FastAPI app (`backend/api/`): businesses, slots, booking status, partner bookings with derived passcodes, PATCH status, slot blocks, doctor leave, HMAC-signed payment webhook, mock pay, dev simulate-booking; async psycopg pool (`backend/store.py`); mock messenger with the WhatsApp card; `scripts/partner_passcodes.py`. Added `docs/FRONTEND_PROMPT.md` plus a frontend ↔ backend differences table in `docs/WEBSITES.md`.
**Tests / checks:** 131 passed (83 new) · ruff ✓ · mypy ✓ · uvicorn smoke boot ✓ (health + simulated booking produced the WhatsApp card).
**Decisions:** backend talks to Postgres directly (`SUPABASE_DB_URL`) for latency + transactions; catalogue text from `data/`, live state from the DB; fuzzy emergency matching uses same-length word windows (fixed "घुटने में दर्द" knee pain matching chest pain).

### 2026-11-22 12:38 IST · Phase 1 · Pranav via Claude Code · done
**Branch:** `main` · **Commits:** `9a2f0b8`
**Done:** `supabase/schema.sql` (tables, partial unique indexes, atomic `book_table` / `book_appointment` / `cancel_booking`, `vaani_today()`), `supabase/rls.sql` (anon read-only, phone columns hidden via column grants, Realtime publication), placeholder data (9 files), `backend/catalog/` (models, loader, validation, schedules, evergreen seed SQL), scripts `validate_data.py`, `make_seed_sql.py`, `seed.py`, `db_apply.py`, `supabase/config.toml`.
**Tests / checks:** 48 passed incl. two 20-caller races (exactly 1 booking each).
**Blockers:** Docker Desktop VM wouldn't start, so RLS/Realtime are not yet verified on local Supabase (`supabase start` → `db_apply.py`).

### 2026-11-22 12:15 IST · Phase 0 · Pranav via Claude Code · done
**Commits:** `d33536a` — repo skeleton, all docs, CLAUDE.md, README, LICENSE, ATTRIBUTIONS, AI_USAGE, EVAL skeleton, `.env.example`, compose skeleton.
