# WHOOP-Alternative — Current State (Technical) · 2026-07-04

A factual record of what we have built and what our data can support. Companion docs:
`WHOOP_SERVERSIDE_ARCHITECTURE.md` (design), `WHOOP_RESEARCH_REFERENCES.md` (brand research + 147 sources),
`WHOOP_FUTURE_STATE_PLAN.md` (research-backed roadmap).

## 1. Architecture
**Self-hosted, server-side.** The phone is a thin **capture + display** client; the RivaFlow VPS is the **brain**.
```
WHOOP 5.0 ─BLE→ Goose iOS app (capture+upload ONLY) ─HTTPS→ RivaFlow VPS ─compute→ /whoop/summary + /view
```
Why (decided 2026-07-04): WHOOP/Oura run proprietary models in their cloud; reproducing that *on-device* hit
the wall of the un-cracked R22/K21 decode. Server-side lets us iterate algorithms in a ~2-min GitOps deploy
with no phone rebuild.

## 2. What we CAPTURE (the biometric surface)
Pipeline: WHOOP 5 → BLE → iOS `WhoopVpsUploader` (GooseBLEClient.swift) → `POST /api/v1/whoop/ingest`
(Bearer, Keychain token) → `WhoopRepository` → Postgres (migration `109_whoop_ingest`). Raw-first + idempotent
(ON CONFLICT DO NOTHING; dedup on `sha256(frame_hex)` / ts).

The upload batch contains **only four arrays** — that is the entire real-time biometric surface:
| Store | Source | Cadence | Notes |
|---|---|---|---|
| `whoop_raw_frames` | **every** BLE notification (proprietary `fd4b0001-0007`, `61080001-0007`, std HR `0x2A37`, battery) | as emitted | Immutable source of truth; hex + char_uuid + fractional-second ISO ts; `decoded=FALSE` for the proprietary optical/IMU streams |
| `whoop_hr` | standard `0x2A37` Heart Rate Measurement (parsed client-side) | ~1 Hz | the only decoded HR stream |
| `whoop_rr` | RR-intervals off `0x2A37` (1/1024 s → ms) | per beat | **the beat-to-beat tachogram — our richest asset** |
| `whoop_battery` | `0x2A19`/`0x2BED` | on change | soc + charging (for wear-time/coverage) |
Plus a phone HR-history uploader backfills up to 48h of the device HR store on connect (overnight coverage).
Current volumes (indicative): ~325k raw frames / ~19k HR / ~13k RR.

## 3. What we COMPUTE today (server-side, `rivaflow/core/whoop_analytics.py`)
All bucketed + displayed in **Australia/Melbourne** local time.
| Metric | Endpoint | Method |
|---|---|---|
| Readiness | `/whoop/readiness` | at-rest RMSSD vs rolling baseline z-score (Plews/Buchheit); Sabbath-silent; 5-day cold-start |
| HRV (RMSSD) | `/whoop/hrv` | resting-band RR (667–1500 ms), successive-diff, outliers>400 ms dropped |
| Resting HR | `/whoop/resting-hr` | 5th-percentile of the day's HR |
| Sleep | `/whoop/sleep` | HR-based window (5-min-bucket median + wake-bridging) + quality vs >9 h need |
| Respiratory rate | `/whoop/respiratory` | RR oscillation (RSA), zero-crossing over resting RR |
| Cardio load / strain | `/whoop/cardio-load` | HR-zone TRIMP, ~0–21 scale |
| Stress | `/whoop/stress` | HR elevation within HR-reserve |
| BJJ session | `/whoop/session-analytics` | HR zones, avg/max, best-60 s recovery |
| One-call rollup | `/whoop/summary` | all of the above |
| Dashboard | `/whoop/view?key=…` | server-rendered HTML (6 cards, 2-min refresh) |
The **slim iOS app** (`SlimHomeView`) fetches `/whoop/summary` and renders it — no on-device compute.
**Known limitation:** `MAX_HR = 190` is hardcoded (44yo generic), which distorts zones/strain/stress for Ruby.

## 4. What our data COULD support but we HAVEN'T built (from the audit)
All reproducible from the HR + RR we already bank:
- **Frequency-domain HRV** (LF, HF, VLF, total power, LF:HF) via FFT/Lomb-Scargle on the resting RR tachogram — sympatho-vagal *balance*, not just RMSSD magnitude.
- **More time-domain + non-linear HRV:** SDNN, pNN50/pNN20, HRV triangular index, **Poincaré SD1/SD2/ratio** (Lorenz plots).
- **DFA α1** — aerobic/anaerobic threshold + durability from exercise RR (research-grade).
- **Full-resolution HR curve** (native ~1 Hz — we currently collapse to a daily percentile).
- **HR-recovery (HRR)** 60 s/120 s post-peak as a standalone fitness/mortality trend (we only compute it per BJJ session).
- **Nocturnal HRV trajectory + sleeping-HR dip / onset**; cardiac drift / aerobic decoupling within a session.
- **Circadian/autonomic rhythm** (time-of-day HR/HRV curves, cosinor amplitude/acrophase, HR-dip at night).
- **Training-load ACWR** (7d acute : 28d chronic) — injury-risk.
- **Multi-signal illness/anomaly detection** (RHR elevation + HRV suppression + respiratory-rate rise, personal-baseline deviation).
- **RR-irregularity screen** (AFib-class) from the nocturnal tachogram — *see the red-team caution in the plan.*
- **Recovery-vs-load coupling** (prior-day load → next-day readiness), **VO₂max estimate** (RHR+HRV+demographics), **wear-time/coverage** analytics.

## 5. What is genuinely LOCKED (needs un-cracked decode)
The proprietary optical (R22/R17) + IMU (K21/K10) frames are **banked raw** (`decoded=FALSE`) but not decoded by any subscription-free project:
- **SpO₂ / blood oxygen** — R22 optical PPG.
- **Skin / peripheral temperature** — temperature-event / NormalHistory family.
- **Steps / motion / actigraphy / posture** — K21 IMU (workaround: iPhone pedometer, deferred).
- **Sleep staging** (light/deep/REM) — needs fused motion + optical.
- **WHOOP's exact cloud scores** (recovery %, strain, sleep score) — closed models; ours are honest independents.
Because the raw is preserved, a future R22/K21 decode retroactively unlocks all of the above from history.

*Current-state audit by the research council, 2026-07-04. Key files: `GooseSwift/GooseBLEClient.swift`, `rivaflow/rivaflow/core/whoop_analytics.py`, `api/routes/whoop.py`, migration `109_whoop_ingest`.*
