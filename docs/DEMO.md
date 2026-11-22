# Vaani — Demo setup and video script

The demo proves "it got the thing done" by showing four things within about 2 seconds: the call, the AI's actions, the business receiving the booking, and the caller getting the confirmation.

## Screens

| Screen | Shows |
|---|---|
| TV | Partner portal in TV mode (`/partner/r/<slug>?tv=1`) for the business being booked; the new booking flashes with a chime |
| Laptop / projector | Live Call Studio (`/studio`): transcript with language tags, slots filling, agent activity timeline, latency meter |
| Caller's phone, mirrored (QuickTime for iPhone, scrcpy for Android) | The live call, then the WhatsApp confirmation card |
| Optional 4th panel | The restaurant's mini-site: the booked slot's count drops live |

## Before going live (checklist)

- [ ] Backend deployed (or local + ngrok) and `GET /health` OK; Twilio voice webhook points at `/twilio/inbound`
- [ ] Data reseeded today (`uv run python scripts/seed.py` — wipes test bookings too) so slots are on current dates and the demo slot (Spice Garden-style restaurant, tomorrow 20:00) is full
- [ ] Click **Enable sound** on the TV portal
- [ ] All team phones (4 + 1 spare) verified on Twilio and joined to the WhatsApp sandbox
- [ ] Studio open and showing the green Live dot
- [ ] Backup video ready on the laptop
- [ ] Invite a judge to call and book while the TV shows the portal

## Video script (~3 minutes, recorded with OBS)

| Time | Segment | What's on screen |
|---|---|---|
| 0:00–0:15 | **Hook:** "One number. Any service. Your language." | Landing page orb, phone dialling |
| 0:15–1:05 | **Hindi restaurant booking:** search → requested slot full → alternative offered → booked → TV flashes + chime → WhatsApp arrives | Phone mirror + Studio + TV |
| 1:05–1:55 | **Telugu hospital appointment:** "skin doctor" → Dermatology → doctor slots → booked → test-mode fee paid → status "Paid" everywhere | Phone + hospital portal + `/b/VN-xxxx` |
| 1:55–2:15 | **Unsupported area + emergency:** polite "only these two areas"; chest-pain phrase → "call 108 / 112", no booking | Studio timeline |
| 2:15–2:40 | **Rush hour:** 4 phones at once in different languages, 4 tiles turn green; load-test table at 1 / 4 / 10 / 15 | Studio tiles grid + `/eval` |
| 2:40–3:00 | **Evidence + vision:** accuracy, latency, naturalness, cost; any business joins as a partner, new services are new playbooks | `/eval`, closing slide |

## Agent activity timeline (what judges should see)

```
11:42:03 Language: Hindi · Service: Restaurant
11:42:05 Searched restaurants → 3 matches in Jubilee Hills (6 people, tomorrow)
11:42:14 Checked Spice Garden slots → 19:30, 20:30 free (20:00 full)
11:42:26 Booked table T4 · 20:30 · ID VN-4821
11:42:27 WhatsApp confirmation sent · Spice Garden notified
```

## Fallbacks

| If… | Then |
|---|---|
| Twilio trial minutes run low | Use browser calls ("Talk to Vaani") for rehearsals; save phone minutes for the recording |
| WhatsApp sandbox session expired | Re-send the join code from each phone the day before; SMS fallback; status page link always works |
| Live call fails on stage | Play the backup video segment, then retry once |
