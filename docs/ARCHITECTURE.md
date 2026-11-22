# Vaani — Architecture

Every call runs through one engine and lands in one database, which pushes changes live to every website.

```
 Phone (any phone)                                   Browser ("Talk to Vaani")
 Twilio number ─ Media Streams websocket             WebRTC via the Pipecat client SDK
                    \                                   /
                     ▼                                 ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Voice server · FastAPI + Pipecat  (one pipeline per live call)          │
 │ VAD + turn detection → streaming STT → LLM → normaliser → streaming TTS │
 │ barge-in · fillers · silence handler · latency logged per turn          │
 ├────────────────────────────────────────────────────────────────────────┤
 │ Conversation flows · Pipecat Flows                                      │
 │   Router (greet, language, intent) → Restaurant agent | Hospital agent  │
 ├────────────────────────────────────────────────────────────────────────┤
 │ Tools · every rule enforced in code                                     │
 │   resolve_area · search_* · get_*_slots · book_* · map_speciality ·     │
 │   answer_faq · send_confirmation · create_payment_link                  │
 ├────────────────────────────────────────────────────────────────────────┤
 │ REST API · Twilio webhooks · payment webhook · dev simulate             │
 └──────────────────────────────┬─────────────────────────────────────────┘
                                │ service key (all writes)
                                ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │ Supabase · Postgres + Realtime + Storage                                │
 │ areas · restaurants · tables · slots · hospitals · doctors · bookings · │
 │ payments · calls · call_events   (atomic booking functions, RLS)        │
 └───────┬───────────────────────────┬─────────────────────────┬──────────┘
         │ anon key, read-only RLS   │                         │
         ▼   + Realtime              ▼                         ▼
 Next.js websites              WhatsApp / SMS (Twilio)     Payments (test mode)
 mini-sites · partner portals  confirmation card           Razorpay / Stripe / mock
 (TV) · studio · logs · eval   "payment received"          → webhook → booking "paid"
```

## Components

| Component | Path | Responsibility |
|---|---|---|
| Transports | `backend/voice/transports/` | Twilio Media Streams (`/ws/twilio`, Pipecat Twilio serializer, DTMF) and WebRTC (`/webrtc/offer`). Same pipeline for both |
| Pipeline | `backend/voice/pipeline.py` | Builds one Pipecat pipeline per call: VAD, turn detection, STT, LLM, normaliser, TTS, barge-in, silence handler, latency observer |
| Provider adapters | `backend/voice/stt.py`, `llm.py`, `tts.py` | Small interfaces chosen by env (`STT_PROVIDER`, `LLM_BASE_URL`/`LLM_MODEL`, `TTS_PROVIDER`) so we can compare stacks |
| Normaliser | `backend/voice/normalizer.py` | Times, dates, ₹ amounts, party sizes → natural spoken te / hi / en-IN before TTS |
| Flows | `backend/flows/` | Router, restaurant and hospital nodes (Pipecat Flows), global functions, shared `CallContext`, prompts per language, text CLI |
| Tools | `backend/tools/` | Implement `CONTRACTS.md` §2; validate everything; write tool timeline; emit `tool_called` |
| Catalog | `backend/catalog/` | Pydantic models for the 9 data files, loader, cross-file validation, slot schedules (`schedule.py`), seed SQL generation |
| Data access | `backend/db.py` (+ repository layer in Phase 2) | Postgres connection + SQL scripts for the scripts/tests; Phase 2 adds a repository interface with Supabase and in-memory implementations |
| Post-call | `backend/postcall/` | Transcript with language tags, outcome JSON, tool timeline, latency, 2-line summary → `calls` |
| API | `backend/api/` | REST endpoints, Twilio webhooks, payment webhook (signature check), dev simulate |
| Eval | `backend/eval/` | `eval.py` (text replay of `test_calls.json`), `load_test.py` (N simulated audio callers) |
| Database | `supabase/` | `schema.sql`, `rls.sql`, `seed.sql` (generated, dates relative to `vaani_today()`), CLI `config.toml`; booking functions lock slot rows; Realtime publication |
| Data | `data/`, `scripts/` | 9 JSON files, `validate_data.py`, `seed.py`, `make_seed_sql.py`, `db_apply.py` |
| Frontend | `frontend/` | Next.js App Router: landing, explore, mini-sites, booking status, mock pay, partner portals (TV), studio, call logs, eval |

## Data flow for one booking

1. Caller speaks → STT → LLM picks `book_table` (only after confirmation).
2. Tool validates and calls Postgres `book_table()` → booking row + updated `restaurant_slots` row in one transaction.
3. Tool emits `booking_created` into `call_events`; Supabase Realtime pushes the `bookings`, `restaurant_slots` and `call_events` changes.
4. Partner portal flashes + chimes, mini-site slot count drops, Studio timeline updates (target < 2 s end to end).
5. `send_confirmation` sends the WhatsApp card with `<site>/b/VN-xxxx`.

## Hosting

| Piece | Where | Why |
|---|---|---|
| Voice server | Fly.io / Render / Railway, region near India (e.g. Mumbai/Singapore) | Long-lived websockets; Vercel can't hold them |
| Frontend | Vercel | Next.js native |
| Database | Supabase (hosted project for the demo; local CLI stack for dev) | |
| Local dev | ngrok for a public `wss://` URL that Twilio can reach | |

## Design principles

- **The LLM talks; code decides.** Nothing the LLM says can create a booking without a tool passing its checks.
- **Swappable providers.** Every external service is behind a small interface + env vars, with a mock for tests.
- **One source of truth.** Contracts in `CONTRACTS.md`; schema in `supabase/schema.sql`; data in `data/`.
