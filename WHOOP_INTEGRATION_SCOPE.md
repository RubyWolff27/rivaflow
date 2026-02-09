# WHOOP Integration — Scoping Document

**Date:** February 2026
**Status:** IMPLEMENTED (Phases 1-3 complete, deployed on main)
**Author:** Claude Opus 4.6

> **Note:** This document was originally a scoping/research doc. All phases have been implemented and deployed as of 2026-02-09. See CHANGELOG.md for release details.

---

## 1. WHOOP API Overview

### Current API Status

WHOOP provides a **public REST API** (WHOOP Developer Platform) with OAuth 2.0 authentication. The API has been publicly available since 2023.

**Base URL:** `https://api.prod.whoop.com/developer/v1`

**Authentication:** OAuth 2.0 Authorization Code Flow
- Users authorise RivaFlow to access their WHOOP data
- Standard OAuth redirect flow
- Access tokens + refresh tokens
- Scopes control data access granularity

### Available Data

| Data Type | Endpoint | Relevance to RivaFlow |
|-----------|----------|----------------------|
| **Recovery** | `/recovery` | Maps directly to Readiness score |
| **Strain** | `/cycle` (strain) | Maps to session intensity |
| **Sleep** | `/sleep` | Maps to Readiness sleep score |
| **Workout** | `/workout` | Could auto-create sessions |
| **Heart Rate** | Within workout data | Maps to whoop_avg_hr, whoop_max_hr |
| **HRV** | Within recovery data | Additional readiness signal |
| **Resting HR** | Within recovery data | Additional readiness signal |
| **Body Measurements** | `/body_measurement` | Maps to weight logging |

### Rate Limits

- 100 requests per minute per user
- Pagination required for historical data
- Webhook support for real-time updates (preferred over polling)

### Cost

- **Free** for developers (no API fees)
- Requires WHOOP membership ($30/month) for users
- No partner program fees for basic integration
- "WHOOP Unite" partner program available for deeper integration (requires application)

---

## 2. Data Mapping: WHOOP → RivaFlow

### Recovery → Readiness

| WHOOP Field | RivaFlow Field | Mapping |
|-------------|---------------|---------|
| `recovery_score` (0-100%) | `composite_score` (4-20) | Scale: `score = 4 + (recovery_score / 100) * 16` |
| `sleep.quality_duration` | `sleep` (1-5) | Duration buckets: <5h=1, 5-6h=2, 6-7h=3, 7-8h=4, 8h+=5 |
| `hrv.current_relative` | Additional signal | Could influence stress score |
| `resting_heart_rate` | Additional signal | Trend analysis for recovery |

### Strain → Session Intensity

| WHOOP Field | RivaFlow Field | Mapping |
|-------------|---------------|---------|
| `strain` (0-21) | `intensity` (1-10) | Scale: `intensity = max(1, min(10, round(strain / 2.1)))` |
| `average_heart_rate` | `whoop_avg_hr` | Direct mapping |
| `max_heart_rate` | `whoop_max_hr` | Direct mapping |
| `kilojoules` | `whoop_calories` | Convert: `calories = kilojoules * 0.239` |
| `strain` | `whoop_strain` | Direct mapping (already exists in sessions table) |

### Body Measurements → Weight

| WHOOP Field | RivaFlow Field | Mapping |
|-------------|---------------|---------|
| `weight_kilogram` | `weight` in weight_logs | Direct mapping |
| `height_meter` | Not used | Could store in profile |

### Workout → Session Auto-Creation

WHOOP workout data could auto-populate session logging:
- `sport_id` → map to `class_type` (WHOOP has sport categories including BJJ)
- `start`/`end` → calculate `duration_mins`
- `strain` → `intensity`
- HR data → WHOOP fields in session

---

## 3. Integration Approach

### Recommended: OAuth + Webhooks (Hybrid)

#### Phase 1: OAuth + On-Demand Sync
```
User clicks "Connect WHOOP" in Settings
  → OAuth redirect to WHOOP authorisation
  → User grants access (scopes: read:recovery, read:sleep, read:workout, read:body_measurement)
  → Callback receives auth code
  → Exchange for access_token + refresh_token
  → Store tokens in user profile (encrypted)
  → Fetch last 7 days of data on initial connect
  → Show WHOOP data in Readiness and Dashboard
```

#### Phase 2: Webhooks (Real-Time)
```
Register webhook with WHOOP API
  → WHOOP sends POST to /api/v1/webhooks/whoop when new data available
  → Backend fetches updated data for that user
  → Auto-updates readiness scores
  → Optionally auto-creates session entries from workouts
```

### Data Sync Frequency
- **Webhooks (preferred):** Real-time, event-driven
- **Polling fallback:** Every 15 minutes for active users, every 6 hours for inactive
- **On-demand:** User can manually trigger sync from Settings

---

## 4. User Experience

### Connect Flow

```
Settings Page:
  ┌─────────────────────────────┐
  │ Connected Devices            │
  │                              │
  │ WHOOP    [Connect WHOOP →]   │
  │                              │
  │ (Future: Apple Health,       │
  │  Google Fit, Garmin)         │
  └─────────────────────────────┘
```

After connecting:
```
  ┌─────────────────────────────┐
  │ Connected Devices            │
  │                              │
  │ WHOOP  ✓ Connected           │
  │ Last synced: 2 mins ago      │
  │ [Sync Now] [Disconnect]      │
  │                              │
  │ Auto-fill readiness: [ON]    │
  │ Auto-create sessions: [OFF]  │
  └─────────────────────────────┘
```

### Readiness Page with WHOOP Data

```
  ┌─────────────────────────────┐
  │ Daily Readiness              │
  │                              │
  │ WHOOP Recovery: 78% 🟢       │
  │ HRV: 45ms  |  RHR: 52bpm    │
  │                              │
  │ Sleep: ████████░░ 7.2h       │
  │ (auto-filled from WHOOP)     │
  │                              │
  │ Stress:  [1] [2] [3] [4] [5]│
  │ Soreness:[1] [2] [3] [4] [5]│
  │ Energy:  [1] [2] [3] [4] [5]│
  │                              │
  │ (Sleep auto-filled, others   │
  │  still manual for now)       │
  └─────────────────────────────┘
```

### Dashboard WHOOP Card

```
  ┌─────────────────────────┐
  │ WHOOP Recovery  78% 🟢   │
  │ Strain: 12.4 | HRV: 45  │
  │ Sleep: 7h 12m            │
  └─────────────────────────┘
```

---

## 5. Competitive Reference

| App | WHOOP Integration | Notes |
|-----|-------------------|-------|
| **Strava** | Workout sync | Auto-creates activities from WHOOP workouts |
| **TrainHeroic** | Recovery + strain | Shows recovery score before workout prescription |
| **TrainingPeaks** | Workout sync | Maps WHOOP workouts to training plan |
| **Volt Athletics** | Recovery | Adjusts workout intensity based on recovery |
| **Cronometer** | Body measurements | Syncs weight data |

### RivaFlow Differentiator
- **BJJ-specific mapping:** WHOOP recovery → BJJ readiness context
- **Fight dynamics correlation:** "Your attack success rate is 20% higher on green recovery days"
- **Partner performance:** "You roll better against [partner] when recovery is above 70%"
- **Comp prep:** Recovery trends leading into competition

---

## 6. Database Changes

```sql
-- User WHOOP connection
ALTER TABLE users ADD COLUMN whoop_access_token TEXT;
ALTER TABLE users ADD COLUMN whoop_refresh_token TEXT;
ALTER TABLE users ADD COLUMN whoop_token_expires_at TIMESTAMP;
ALTER TABLE users ADD COLUMN whoop_user_id TEXT;
ALTER TABLE users ADD COLUMN whoop_connected_at TIMESTAMP;
ALTER TABLE users ADD COLUMN whoop_last_synced_at TIMESTAMP;

-- WHOOP data cache (avoid re-fetching)
CREATE TABLE whoop_daily_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    recovery_score REAL,
    strain REAL,
    sleep_duration_mins INTEGER,
    sleep_quality_duration_mins INTEGER,
    hrv REAL,
    resting_hr INTEGER,
    max_hr INTEGER,
    avg_hr INTEGER,
    calories INTEGER,
    raw_data TEXT, -- JSON blob of full WHOOP response
    synced_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE(user_id, date)
);
```

---

## 7. Implementation Files

### Backend
```
rivaflow/api/routes/integrations.py     # OAuth callback, sync, webhook endpoints
rivaflow/core/services/whoop_service.py # WHOOP API client, data mapping
rivaflow/db/repositories/whoop_repo.py  # WHOOP data storage
rivaflow/db/migrations/0XX_whoop.sql    # Schema changes
```

### Frontend
```
web/src/pages/Settings.tsx              # Add "Connected Devices" section
web/src/components/WhoopCard.tsx        # Dashboard recovery card
web/src/api/client.ts                   # Add integrationsApi methods
```

### Environment Variables
```
WHOOP_CLIENT_ID=...
WHOOP_CLIENT_SECRET=...
WHOOP_REDIRECT_URI=https://rivaflow.app/api/v1/integrations/whoop/callback
WHOOP_WEBHOOK_SECRET=...
```

---

## 8. Effort Estimate

| Task | Effort | Priority |
|------|--------|----------|
| WHOOP developer account + app registration | 1 hour | P0 |
| OAuth flow (backend + frontend) | 4 hours | P0 |
| WHOOP API client service | 4 hours | P0 |
| Data mapping + readiness auto-fill | 3 hours | P0 |
| Dashboard WHOOP card | 2 hours | P1 |
| Webhook integration | 3 hours | P1 |
| Settings UI (connect/disconnect) | 2 hours | P0 |
| Session auto-creation from workouts | 4 hours | P2 |
| Testing + edge cases | 4 hours | P0 |
| Weight sync | 1 hour | P2 |

**Total: ~28 hours (4-5 days)**

---

## 9. Risks & Considerations

### Technical Risks
- **API changes:** WHOOP API is relatively new; endpoints may change
- **Rate limits:** 100 req/min may be limiting with many users
- **Token refresh:** Need robust token refresh handling (tokens expire)
- **Data gaps:** WHOOP data may have gaps (device not worn, charging)

### Business Risks
- **Small user base overlap:** Not all BJJ athletes use WHOOP (~$30/month device)
- **Dependency on third-party:** WHOOP could restrict API access
- **Support burden:** OAuth issues, sync problems = support tickets

### Privacy Considerations
- WHOOP data is health data (sensitive under Australian Privacy Act)
- Users must explicitly consent to data sharing
- Must provide easy disconnect/data deletion
- Store tokens encrypted at rest

---

## 10. Implementation Status

**All phases implemented and deployed (2026-02-09):**

| Phase | Status | Description |
|-------|--------|-------------|
| Phase 1 | Done | OAuth + workout sync + session overlay |
| Phase 2 | Done | Recovery sync, webhooks, readiness auto-fill, HRV/RHR trends |
| Phase 3 | Done | Recovery-aware AI coaching, 6-factor overtraining, sport science analytics engine, session WHOOP context, Performance Science frontend charts |

### Phase 3 Details (latest)

**Sport Science Analytics Engine** (`whoop_analytics_engine.py`):
- Recovery-Performance Correlation (Pearson r + zone bucketing)
- Strain Efficiency (submissions/strain by class type and gym)
- HRV Performance Predictor (optimal HRV threshold detection)
- Sleep Impact Analysis (REM/SWS/total sleep correlation)
- Cardiovascular Drift (weekly RHR trend classification)

**Recovery-Aware AI**: Grapple AI system prompt includes WHOOP recovery data, HRV trends, sleep metrics. Post-session and weekly insights enriched with biometrics.

**Enhanced Overtraining Detection**: 6 factors (was 4) — added HRV decline (max 15) and low recovery streak (max 15). Non-WHOOP users unaffected.

**Session Detail**: Recovery Context Card + HR Zone Distribution per session.

**Frontend**: 5 Performance Science chart components on Readiness tab.

**API Endpoints**:
- `GET /analytics/whoop/performance-correlation`
- `GET /analytics/whoop/efficiency`
- `GET /analytics/whoop/cardiovascular`
- `GET /integrations/whoop/session/{id}/context`

---

*Implementation verified with 298 passing tests, full CI green (black, ruff, tsc, pytest).*
