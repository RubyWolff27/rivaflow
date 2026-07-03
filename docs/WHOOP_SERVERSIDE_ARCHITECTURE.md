# WHOOP (subscription-free) — Server-Side Architecture

**Decided 2026-07-04:** WHOOP/Oura do the heavy compute in the *cloud*; the wearable is capture+display.
We do the same, self-hosted. **The phone is a thin capture client; RivaFlow (VPS) is the brain; a URL is
the display.** No on-device derivation (that was the source of the app's lag).

```
WHOOP 5.0 strap ──BLE──▶ Goose iOS app (capture + upload ONLY) ──HTTPS──▶ RivaFlow VPS
                                                                              │ compute (whoop_analytics.py)
                                                                              ▼
                                                        /api/v1/whoop/summary + /view (server-rendered HTML)
```

## What the VPS computes (all from HR + RR we already capture)
`rivaflow/core/whoop_analytics.py`, exposed via `api/routes/whoop.py`:

| Metric | Endpoint | Method | Benchmark |
|---|---|---|---|
| Readiness | `/whoop/readiness` | at-rest HRV vs rolling baseline (Plews/Buchheit); Sabbath-silent | WHOOP recovery |
| HRV (RMSSD) | `/whoop/hrv` | resting RR successive-diff | WHOOP/Oura HRV |
| Resting HR | `/whoop/resting-hr` | 5th-percentile of daily HR | Oura RHR |
| Sleep | `/whoop/sleep` | HR-based window (5-min bucket median + wake-bridging) + quality vs >9h need | Oura/WHOOP sleep* |
| Respiratory rate | `/whoop/respiratory` | RR oscillation (RSA) | Oura resp rate |
| Cardio load / strain | `/whoop/cardio-load` | HR-zone TRIMP, ~0–21 | WHOOP strain |
| Stress | `/whoop/stress` | HR elevation within reserve | WHOOP/Hume stress |
| Steps | *TODO* | iPhone pedometer (CoreMotion/HealthKit) → upload | Oura/WHOOP steps |
| **One-call rollup** | `/whoop/summary` | all of the above | — |
| **Dashboard** | `/whoop/view?key=rf_pk_…` | server-rendered HTML, auto-refresh 2 min | — |

\* HR-based sleep = honest duration/timing, NOT WHOOP's proprietary sleep *staging*.

## Genuinely out of reach (locked)
- **SpO₂, skin temperature** — need the R22 optical/vitals decode no subscription-free project has cracked.
- **Band steps / motion** — need the K21 IMU decode (same tier). → use the iPhone pedometer instead.
- WHOOP's *exact* cloud scores — proprietary models; ours are honest independent equivalents.

## Timezone
All day-bucketing + display use **Australia/Melbourne** (`_local_day`/`_local_hm`), single `LOCAL_TZ`
constant. TODO(travel): phone sends `TimeZone.current.identifier` per-ingest → server uses the device tz.

## Deploy
Push `RubyWolff27/rivaflow` main → GitOps auto-deploy (~2–3 min). Server-side iteration is the win:
fixing the sleep algorithm took one 2-minute deploy, no phone build.

## Remaining
1. **Slim the goose app** — one screen: band connection/throughput + key data (fetch `/whoop/summary`) +
   Start Workout + iPhone-pedometer steps capture. Strip Health/Coach/debug + all on-device compute.
   (Paired UI build — needs on-device visual verification.)
2. **Device timezone for travel** (small: phone→ingest tz).
3. **Refinements:** respiratory rate over the sleep window (more accurate); sleep staging if R22 ever decodes.
4. Rotate the exposed api key.

*Consolidated 2026-07-04.*
