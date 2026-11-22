# Vaani frontend

Next.js frontend for the Vaani voice booking demo. This standalone Phase 1
checkpoint is laid out to be copied into the shared repository as `frontend/`.

## Run locally

Requires Node.js 20.9 or newer.

```sh
npm ci
cp .env.example .env.local
npm run dev
```

Open http://localhost:3000. On Windows PowerShell, use
`Copy-Item .env.example .env.local` to copy the environment template.

Mock mode requires no credentials. The root page previews the public shell and
English, Telugu and Hindi content. The data layer exposes 20 fictional
businesses, seven days of slots in IST, restaurant table allocation, doctor
appointments, cancellations, slot blocks and doctor leave.

Mock browser writes are stored per origin in local storage. Realtime events
reach open tabs on the same origin and browser profile. Cross-device sync
requires the live adapter. Browsers supporting Web Locks serialize writes
across tabs. Server-side mock writes are process-local and intended for tests.

## Environment

| Variable | Purpose |
| --- | --- |
| `NEXT_PUBLIC_DATA_MODE` | `mock` now. `live` is reserved for Phase 6. |
| `NEXT_PUBLIC_BACKEND_URL` | FastAPI and WebRTC base URL |
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase project endpoint |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Public Supabase key for RLS-protected access |
| `NEXT_PUBLIC_VAANI_PHONE` | Demo telephone number |
| `NEXT_PUBLIC_DEV_SIMULATE` | Controls simulator buttons once those screens are built |
| `PARTNER_PASSCODES` | Server-only JSON map for demo login once the partner routes are built |

## Checks

```sh
npm run lint
npm run typecheck
npx playwright install chromium
npm run test:e2e
npm run build
```

Set `VAANI_CHROMIUM_PATH` if using a system Chromium instead of Playwright’s
bundled browser. Native speakers should verify the Telugu and Hindi copy before
the demo.

## Phases

1. Foundation, the current checkpoint.
2. Public directory, mini-sites, status and test payment.
3. Partner portals, schedules, actions and TV mode.
4. Studio, replay, logs and evaluation.
5. 3D orb, accessibility, performance and demo media.
6. Live Supabase and FastAPI adapters, Pipecat and deployment.
