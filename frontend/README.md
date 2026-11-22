# Vaani public landing page

From `frontend/`, run `npm ci` and `npm run dev` with Node.js 20.9 or newer.
Open http://localhost:3000.

The sample-call dialog uses scripted text. If a demo phone line is available,
configure `NEXT_PUBLIC_VAANI_PHONE` in `.env.local` in E.164 format and restart
the server. This enables a device phone link.

Run `npm run lint`, `npm run typecheck` and `npm run build` to check the app.

Typography uses Inter and Anek Telugu and Devanagari (SIL Open Font License).
The waveform illustration is original vector artwork.
