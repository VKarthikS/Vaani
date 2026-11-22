# Vaani — Evaluation

Every number here is measured, split by Telugu (te-en), Hindi (hi-en) and Indian English (en-IN), and mirrored on the `/eval` page.

> Status: skeleton. Numbers are filled from Phase 3 (text eval) and Phase 7 (voice, load, live sync).

## How we measure

- **`backend/eval/eval.py`** replays the 40 scripted calls in `data/test_calls.json` as text turns through the real flows and tools (fast, no audio) and stores a results table.
- **`backend/eval/load_test.py`** streams recorded audio through N simulated callers (1 / 4 / 10 / 15) and records latency and success.
- **Naturalness:** blind 1–5 ratings by 10 people over real calls.
- **Live sync:** timestamp of `booking_created` vs. first render on the partner portal, mini-site and WhatsApp delivery.

## Targets and results

| Metric | Target | te-en | hi-en | en-IN | All |
|---|---|---|---|---|---|
| Booking accuracy (area, business, doctor, date, time, party size all correct) | ≥ 85–90% | TBD | TBD | TBD | TBD |
| Expected business in top 3 | ≥ 90% | TBD | TBD | TBD | TBD |
| Unsupported area handled | 100% | TBD | TBD | TBD | TBD |
| Emergency → 108/112, no booking | 100% | TBD | TBD | TBD | TBD |
| Slot full → 2 nearest offered | ≥ 90% | TBD | TBD | TBD | TBD |
| Time to first audio (median / slowest) | ~1 s / < 2 s | TBD | TBD | TBD | TBD |
| Stop speaking on interruption | < 0.5 s | | | | TBD |
| Naturalness (blind 1–5, 10 people) | ≥ 4 | TBD | TBD | TBD | TBD |
| Live sync call → portal + mini-site + WhatsApp | < 2 s | | | | TBD |
| Cost per call minute (telephony + STT + LLM + TTS) | report | | | | TBD |

## Load test

| Concurrent callers | Median time to first audio | Slowest | Success % |
|---|---|---|---|
| 1 | TBD | TBD | TBD |
| 4 | TBD | TBD | TBD |
| 10 | TBD | TBD | TBD |
| 15 | TBD | TBD | TBD |

## Stack comparisons

_STT / LLM / TTS candidates compared on latency, accuracy and cost go here._

## Verification matrix

| Requirement | How verified | Result |
|---|---|---|
| No double booking under concurrency | `backend/tests/test_db_booking.py`: 20 concurrent callers on one doctor slot and on a restaurant's only 12-seat table | ✅ exactly 1 success, 19 `SLOT_TAKEN` / `SLOT_FULL` (Phase 1, Postgres 15) |
| Booking rules enforced in the database | same file: slot full, blocked, party limit, doctor leave, past time, unknown business, cancel frees slot | ✅ (Phase 1) |
| Data integrity | `scripts/validate_data.py` + 15 mutation tests | ✅ placeholder set: 0 errors, 0 warnings |
| Blocked slot refused by the AI | E2E test (Phase 7) | TBD |
| Booking visible everywhere < 2 s | E2E test (Phase 7) | TBD |
