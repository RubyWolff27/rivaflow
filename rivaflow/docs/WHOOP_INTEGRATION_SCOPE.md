# WHOOP Wearable Integration -- Scoping Document

**Project:** RivaFlow (BJJ Training Tracker)
**Author:** Engineering Team
**Date:** 2026-02-07
**Status:** Draft / Scoping
**Version:** 1.0

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [WHOOP API Status](#2-whoop-api-status)
3. [Data Mapping to RivaFlow](#3-data-mapping-to-rivaflow)
4. [Integration Approach](#4-integration-approach)
5. [Technical Architecture](#5-technical-architecture)
6. [User Experience](#6-user-experience)
7. [Cost and Rate Limits](#7-cost-and-rate-limits)
8. [Competitive Reference](#8-competitive-reference)
9. [Risks and Mitigations](#9-risks-and-mitigations)
10. [Recommendation](#10-recommendation)
11. [Effort Estimate](#11-effort-estimate)
12. [Appendix](#12-appendix)

---

## 1. Executive Summary

This document scopes a full WHOOP wearable integration for RivaFlow, our BJJ training
tracker application. The integration would allow RivaFlow users who own a WHOOP strap
to automatically pull recovery, sleep, strain, and heart rate data into RivaFlow, enriching
the existing readiness model and providing data-driven training recommendations.

RivaFlow already has partial WHOOP support: the `sessions` table contains `whoop_strain`,
`whoop_calories`, `whoop_avg_hr`, and `whoop_max_hr` columns (migration 011), and
the `readiness_analytics.py` service includes a `get_whoop_analytics()` method. However,
all WHOOP data is currently entered manually by the user. This integration would replace
manual entry with automated API-driven data synchronization.

WHOOP offers a mature, OAuth 2.0-based REST API (v2 as of July 2025) with endpoints for
recovery, sleep, cycles, workouts, and body measurements. The API is free to access, supports
webhooks for real-time event notifications, and imposes reasonable rate limits (100 req/min,
10,000 req/day). This makes a direct integration technically feasible and cost-effective.

---

## 2. WHOOP API Status

### 2.1 Platform Overview

The WHOOP Developer Platform (https://developer.whoop.com) provides a public REST API that
enables third-party applications to access physiological data collected 24/7 by the WHOOP
wearable strap. The platform launched its v2 API in July 2025, with improved data models and
UUID-based resource identifiers replacing the integer IDs used in v1.

- **API Base URL (v1):** `https://api.prod.whoop.com/developer/v1/`
- **API Base URL (v2):** `https://api.prod.whoop.com/developer/v2/`
- **Authentication:** OAuth 2.0 (RFC 6749)
- **Data Format:** JSON
- **Pagination:** Cursor-based, results sorted by start time descending
- **API Version:** v2 (recommended); v1 still functional but deprecated

### 2.2 Available Endpoints and Data

| Endpoint Category   | HTTP Method | Path (v1)                             | Key Data Fields                                                                      |
|---------------------|-------------|---------------------------------------|--------------------------------------------------------------------------------------|
| **User Profile**    | GET         | `/v1/user/profile/basic`              | `user_id`, `first_name`, `last_name`, `email`                                        |
| **Body Measurement**| GET         | `/v1/user/measurement/body`           | `height_meter`, `weight_kilogram`, `max_heart_rate`                                  |
| **Cycles**          | GET         | `/v1/cycle`                           | `id`, `start`, `end`, `strain` (day strain 0-21), `kilojoules`, `avg_hr`, `max_hr`   |
| **Recovery**        | GET         | `/v1/recovery`                        | `cycle_id`, `score` (0-100%), `hrv` (ms), `resting_heart_rate`, `spo2`               |
| **Sleep**           | GET         | `/v1/activity/sleep`                  | `id`, `start`, `end`, `score` (sleep performance), `stage_summary` (wake/light/deep/REM durations) |
| **Workouts**        | GET         | `/v1/activity/workout`                | `id`, `sport_id`, `start`, `end`, `strain`, `avg_hr`, `max_hr`, `kilojoules`, `zones`|
| **Activity Mapping**| GET         | `/v1/activity-mapping/{activityV1Id}` | Maps v1 integer IDs to v2 UUIDs                                                     |
| **OAuth Revoke**    | DELETE      | `/v1/user/oauth/revoke`               | Revokes access token and stops webhooks                                              |

**Note on v2:** The v2 API uses UUIDs for sleep and workout resources. Recovery in v2 is
keyed by the UUID of the associated sleep (not the cycle ID as in v1). All new integrations
should target v2 and use the migration mapping endpoint if backward compatibility is needed.

### 2.3 Recovery Data (Primary Interest)

The Recovery endpoint returns the following fields, which are the most valuable for RivaFlow:

```json
{
  "cycle_id": 93845749384,
  "sleep_id": "a1b2c3d4-...",
  "user_id": 10129,
  "created_at": "2026-02-06T07:30:00.000Z",
  "updated_at": "2026-02-06T07:35:00.000Z",
  "score_state": "SCORED",
  "score": {
    "user_calibrating": false,
    "recovery_score": 84.0,
    "resting_heart_rate": 52.0,
    "hrv_rmssd_milli": 68.432,
    "spo2_percentage": 97.2,
    "skin_temp_celsius": 33.1
  }
}
```

Key fields:
- **`recovery_score`** (0-100%): Primary readiness indicator. Green >= 67%, Yellow 34-66%, Red <= 33%.
- **`hrv_rmssd_milli`** (ms): Root mean square of successive differences, measured during deepest sleep.
- **`resting_heart_rate`** (bpm): Measured at rest during sleep.
- **`spo2_percentage`**: Blood oxygen saturation.
- **`skin_temp_celsius`**: Skin temperature baseline.

### 2.4 Sleep Data

```json
{
  "id": "uuid-...",
  "start": "2026-02-05T23:15:00.000Z",
  "end": "2026-02-06T07:00:00.000Z",
  "score": {
    "stage_summary": {
      "total_in_bed_time_milli": 27900000,
      "total_awake_time_milli": 3600000,
      "total_light_sleep_time_milli": 10800000,
      "total_slow_wave_sleep_time_milli": 5400000,
      "total_rem_sleep_time_milli": 8100000,
      "sleep_cycle_count": 5
    },
    "sleep_needed": { "baseline_milli": 28800000 },
    "respiratory_rate": 15.2,
    "sleep_performance_percentage": 85.0,
    "sleep_consistency_percentage": 78.0,
    "sleep_efficiency_percentage": 88.5
  }
}
```

### 2.5 Workout Data

```json
{
  "id": "uuid-...",
  "sport_id": 84,
  "start": "2026-02-06T18:00:00.000Z",
  "end": "2026-02-06T19:30:00.000Z",
  "score": {
    "strain": 14.2,
    "average_heart_rate": 152,
    "max_heart_rate": 185,
    "kilojoule": 1843.5,
    "zone_duration": {
      "zone_zero_milli": 0,
      "zone_one_milli": 300000,
      "zone_two_milli": 900000,
      "zone_three_milli": 1800000,
      "zone_four_milli": 1200000,
      "zone_five_milli": 600000
    }
  }
}
```

WHOOP sport IDs relevant to BJJ:
- **84**: Martial Arts (general)
- **87**: Brazilian Jiu-Jitsu (if available as distinct category)
- **86**: Wrestling
- **41**: Yoga
- **1**: Running (for S&C cross-training)

### 2.6 OAuth 2.0 Details

| Parameter            | Value                                                    |
|----------------------|----------------------------------------------------------|
| Authorization URL    | `https://api.prod.whoop.com/oauth/oauth2/auth`           |
| Token URL            | `https://api.prod.whoop.com/oauth/oauth2/token`          |
| Grant Type           | Authorization Code                                       |
| Access Token Expiry  | 3,600 seconds (1 hour)                                   |
| Refresh Token        | Requires `offline` scope; no documented expiry            |
| Redirect URL         | Must be registered in WHOOP Developer Dashboard           |
| State Parameter      | Required (CSRF protection)                                |

**Available Scopes:**

| Scope                    | Description                                   |
|--------------------------|-----------------------------------------------|
| `offline`                | Enables refresh tokens for persistent access  |
| `read:profile`           | User profile (name, email)                    |
| `read:body_measurement`  | Height, weight, max heart rate                |
| `read:recovery`          | Recovery scores, HRV, resting HR              |
| `read:cycles`            | Physiological cycle data (day strain)         |
| `read:sleep`             | Sleep stages, performance, duration           |
| `read:workout`           | Workout strain, HR zones, calories            |

**Scopes RivaFlow would request:**
`offline read:recovery read:sleep read:workout read:cycles read:body_measurement`

We deliberately omit `read:profile` since we do not need the user's WHOOP name/email --
RivaFlow has its own user identity system.

### 2.7 Webhooks

WHOOP supports webhooks (v2) for event-driven notifications. When a workout, sleep, or
recovery is created or updated, WHOOP sends an HTTP POST to your registered webhook URL
with event metadata (not the full payload). You must then call the API to fetch the
updated data.

**Webhook event types:**
- `workout.updated` -- A workout was created or modified
- `sleep.updated` -- A sleep record was created or modified
- `recovery.updated` -- A recovery score was created or modified

**Important:** v2 webhooks use UUIDs as identifiers. Recovery webhooks reference the
UUID of the associated sleep, not the cycle ID.

Webhooks are configured per OAuth client in the WHOOP Developer Dashboard and require a
publicly reachable HTTPS endpoint.

---

## 3. Data Mapping to RivaFlow

### 3.1 Current RivaFlow Readiness Model

RivaFlow's existing readiness check-in captures the following (all 1-5 integer scale):

| Field          | Scale | Description                          |
|----------------|-------|--------------------------------------|
| `sleep`        | 1-5   | Subjective sleep quality             |
| `stress`       | 1-5   | Perceived stress level (5 = high)    |
| `soreness`     | 1-5   | Muscle soreness level (5 = very sore)|
| `energy`       | 1-5   | Energy level (5 = high energy)       |
| `hotspot_note` | text  | Injury/pain location note            |
| `weight_kg`    | float | Body weight in kilograms             |

**Composite score formula:** `sleep + (6 - stress) + (6 - soreness) + energy` (range 4-20)

### 3.2 WHOOP-to-RivaFlow Mapping

```
WHOOP Data                          RivaFlow Field              Transformation
-----------------------------------+---------------------------+-------------------------------------
Recovery Score (0-100%)             | readiness.sleep           | Map to 1-5 scale (see below)
                                    | + auto-populate energy    |
Sleep Performance (0-100%)          | readiness.sleep           | Map to 1-5 scale
Sleep Duration vs Need              | (informational)           | Display in readiness card
HRV (ms, rmssd)                     | NEW: readiness.hrv_ms     | Store raw value
Resting Heart Rate (bpm)            | NEW: readiness.resting_hr | Store raw value
SpO2 (%)                            | NEW: readiness.spo2       | Store raw value
Skin Temperature (C)                | (informational)           | Display in trends only
Day Strain (0-21)                   | sessions.whoop_strain     | Already exists in schema
Workout Strain (0-21)               | sessions.whoop_strain     | Already exists in schema
Workout Avg HR                      | sessions.whoop_avg_hr     | Already exists in schema
Workout Max HR                      | sessions.whoop_max_hr     | Already exists in schema
Workout Calories (kJ -> kcal)       | sessions.whoop_calories   | Convert kJ to kcal (x 0.239)
Body Weight (kg)                    | readiness.weight_kg       | Already exists in schema
Body Max Heart Rate                 | (informational)           | Display in profile
```

### 3.3 Recovery Score to Readiness Scale Conversion

WHOOP's Recovery Score (0-100%) maps to RivaFlow's composite readiness model as follows:

```
WHOOP Recovery     WHOOP Color     RivaFlow       RivaFlow
Score Range        Zone            Sleep (1-5)    Energy (1-5)    Composite Impact
-----------------+--------------+--------------+--------------+------------------
 90 - 100%         Green           5              5               Excellent (17-20)
 67 -  89%         Green           4              4               Good (14-16)
 50 -  66%         Yellow          3              3               Moderate (11-13)
 34 -  49%         Yellow          2              2               Low (8-10)
  1 -  33%         Red             1              1               Very Low (4-7)
```

**Design decision:** When WHOOP data is available, the `sleep` and `energy` fields are
auto-populated from the recovery score. The `stress` and `soreness` fields remain
user-entered because WHOOP cannot measure perceived psychological stress or localized
muscle soreness. This hybrid approach preserves the value of subjective self-reporting
while enriching it with objective physiological data.

### 3.4 New Database Columns (readiness table)

```sql
-- Migration: 0XX_add_whoop_readiness_fields.sql

ALTER TABLE readiness ADD COLUMN hrv_ms REAL;
ALTER TABLE readiness ADD COLUMN resting_hr INTEGER;
ALTER TABLE readiness ADD COLUMN spo2 REAL;
ALTER TABLE readiness ADD COLUMN whoop_recovery_score REAL;
ALTER TABLE readiness ADD COLUMN whoop_sleep_score REAL;
ALTER TABLE readiness ADD COLUMN data_source VARCHAR(20) DEFAULT 'manual';
  -- Values: 'manual', 'whoop', 'whoop+manual' (user overrode WHOOP values)
```

### 3.5 New Database Table (WHOOP tokens)

```sql
-- Migration: 0XX_add_whoop_integration.sql

CREATE TABLE whoop_connections (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    whoop_user_id VARCHAR(100),
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_expires_at TIMESTAMP NOT NULL,
    scopes TEXT NOT NULL,
    connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_sync_at TIMESTAMP,
    sync_status VARCHAR(20) DEFAULT 'active',
      -- Values: 'active', 'expired', 'revoked', 'error'
    sync_error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id)
);

CREATE INDEX idx_whoop_connections_user ON whoop_connections(user_id);
CREATE INDEX idx_whoop_connections_status ON whoop_connections(sync_status);
```

---

## 4. Integration Approach

### 4.1 OAuth 2.0 Authorization Flow

```
+------------------+                              +--------------------+
|                  |  1. User clicks              |                    |
|   RivaFlow Web   |     "Connect WHOOP"          |   WHOOP OAuth      |
|   (Settings)     +----------------------------->|   Authorization    |
|                  |                              |   Server           |
|                  |                              |                    |
|                  |  2. Redirect to WHOOP login  |                    |
|                  |     with scopes + state      |                    |
|                  |                              +--------+-----------+
|                  |                                       |
|                  |                              3. User logs in to
|                  |                                 WHOOP and approves
|                  |                                 requested scopes
|                  |                                       |
|                  |  4. Redirect back to         +--------+-----------+
|                  |     RivaFlow callback         |                    |
|                  |     with auth code + state    |   WHOOP OAuth      |
|                  |<-----------------------------+   Authorization    |
|                  |                              |   Server           |
+--------+---------+                              +--------------------+
         |
         | 5. RivaFlow backend exchanges
         |    auth code for tokens
         v
+--------+---------+                              +--------------------+
|                  |  POST /oauth/oauth2/token    |                    |
|   RivaFlow API   +----------------------------->|   WHOOP Token      |
|   (Backend)      |  grant_type=authorization    |   Endpoint         |
|                  |  _code + code + redirect_uri |                    |
|                  |                              |                    |
|                  |  6. Receive access_token,    |                    |
|                  |     refresh_token,           |                    |
|                  |     expires_in               |                    |
|                  |<-----------------------------+                    |
|                  |                              +--------------------+
+--------+---------+
         |
         | 7. Encrypt tokens, store in
         |    whoop_connections table
         | 8. Trigger initial data sync
         v
+--------+---------+
|                  |
|   PostgreSQL     |
|   (Encrypted     |
|    Token Store)  |
|                  |
+------------------+
```

### 4.2 Data Sync Strategy

The integration uses a **dual-mode synchronization** approach:

1. **Webhooks (primary, near-real-time):** WHOOP sends event notifications when recovery,
   sleep, or workout data is created or updated. RivaFlow receives the webhook, then calls
   the WHOOP API to fetch the full data payload.

2. **Polling (fallback, daily):** A scheduled background job runs once daily (e.g., 08:00 UTC)
   to catch any missed webhook events, handle token refresh, and perform data reconciliation.

```
+---------------------+     Webhook POST      +---------------------+
|                     |  (event notification)  |                     |
|   WHOOP Platform    +----------------------->|   RivaFlow API      |
|                     |                        |   /webhooks/whoop   |
+---------------------+                        +---------+-----------+
                                                         |
                                               Parse event type
                                               Verify signature
                                                         |
                                                         v
                                               +---------+-----------+
                                               |                     |
                                               |   Event Router      |
                                               |                     |
                                               +--+------+-------+--+
                                                  |      |       |
                                      +-----------+  +---+---+  ++----------+
                                      |              |       |   |          |
                                      v              v       v   v          |
                               +------+---+  +------+--+ +--+---+---+      |
                               | Recovery |  |  Sleep   | | Workout  |      |
                               | Handler  |  | Handler  | | Handler  |      |
                               +------+---+  +------+---+ +----+----+      |
                                      |             |           |           |
                                      v             v           v           |
                               +------+-------------+-----------+---+      |
                               |                                    |      |
                               |   WHOOP API Client                 |      |
                               |   (fetch full data by ID)          |      |
                               |                                    |      |
                               +----------------+-------------------+      |
                                                |                          |
                                                v                          |
                               +----------------+-------------------+      |
                               |                                    |      |
                               |   Data Transformation Layer        |<-----+
                               |   (WHOOP -> RivaFlow models)       |
                               |                                    |
                               +----------------+-------------------+
                                                |
                                                v
                               +----------------+-------------------+
                               |                                    |
                               |   RivaFlow Database                |
                               |   (readiness / sessions tables)    |
                               |                                    |
                               +------------------------------------+
```

### 4.3 Daily Polling Job (Fallback / Reconciliation)

```
+-------------------------------------------------------------------+
|   DAILY SYNC JOB (runs at 08:00 UTC via cron / task scheduler)    |
+-------------------------------------------------------------------+
         |
         v
  +------+--------+
  | Load all      |     For each active connection:
  | active WHOOP  +--+
  | connections   |  |
  +-----------+---+  |
              |      |
              v      |
  +-----------+---+  |  +-----------------------+
  | Refresh token |  |  | If token refresh      |
  | if expired    |  |  | fails, mark connection|
  | (1hr expiry)  |  +->| as 'expired' and      |
  +-----------+---+     | notify user           |
              |         +-----------------------+
              v
  +-----------+----------+
  | Fetch latest:        |
  |  - Recovery (today)  |
  |  - Sleep (last night)|
  |  - Workouts (today)  |
  |  - Body measurements |
  +-----------+----------+
              |
              v
  +-----------+----------+
  | Transform + upsert   |
  | into RivaFlow tables |
  +-----------+----------+
              |
              v
  +-----------+----------+
  | Update last_sync_at  |
  | on whoop_connections |
  +----------------------+
```

### 4.4 Token Management

- **Encryption:** Access and refresh tokens are encrypted at rest using AES-256-GCM
  (via Python `cryptography` library) with a key derived from the application's
  `SECRET_KEY` environment variable.
- **Refresh:** Before any API call, check if `token_expires_at < now()`. If expired,
  use the refresh token to obtain a new access token. Update the stored tokens.
- **Revocation:** When a user disconnects WHOOP, call the WHOOP revocation endpoint
  (`DELETE /v1/user/oauth/revoke`) and delete the `whoop_connections` row.
- **Error handling:** If a refresh token is rejected (user revoked access on WHOOP side),
  mark the connection as `revoked`, clear stored tokens, and display a reconnection
  prompt in the UI.

---

## 5. Technical Architecture

### 5.1 New Backend Components

```
rivaflow/
  integrations/
    __init__.py
    whoop/
      __init__.py
      client.py              # WHOOP API HTTP client (httpx-based)
      oauth.py               # OAuth flow handlers (auth URL, callback, token exchange)
      token_manager.py       # Token encryption, storage, refresh logic
      sync_service.py        # Data sync orchestration (webhook + polling)
      transformers.py        # WHOOP -> RivaFlow data transformation
      webhook_handler.py     # Webhook endpoint and event routing
      constants.py           # Sport IDs, scope strings, URLs

  api/routes/
    whoop.py                 # New API routes: /whoop/connect, /whoop/callback, etc.

  db/
    repositories/
      whoop_repo.py          # CRUD for whoop_connections table
    migrations/
      0XX_add_whoop_integration.sql
      0XX_add_whoop_readiness_fields.sql
```

### 5.2 API Endpoints (RivaFlow)

| Method | Path                        | Description                                      |
|--------|-----------------------------|--------------------------------------------------|
| GET    | `/api/whoop/connect`        | Generate WHOOP OAuth URL, redirect user           |
| GET    | `/api/whoop/callback`       | OAuth callback, exchange code for tokens          |
| DELETE | `/api/whoop/disconnect`     | Revoke tokens, remove connection                  |
| GET    | `/api/whoop/status`         | Connection status, last sync time, errors         |
| POST   | `/api/whoop/sync`           | Manual sync trigger (on-demand)                   |
| POST   | `/api/webhooks/whoop`       | Webhook receiver (called by WHOOP platform)       |

### 5.3 WHOOP API Client

```python
# rivaflow/integrations/whoop/client.py (simplified)

import httpx
from datetime import datetime, timedelta

class WhoopClient:
    """HTTP client for WHOOP API v1."""

    BASE_URL = "https://api.prod.whoop.com/developer/v1"

    def __init__(self, access_token: str):
        self.session = httpx.Client(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=30.0,
        )

    def get_recovery(self, start: datetime, end: datetime) -> list[dict]:
        """Fetch recovery records within a date range."""
        params = {
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
        }
        return self._paginate("/v1/recovery", params)

    def get_sleep(self, start: datetime, end: datetime) -> list[dict]:
        """Fetch sleep records within a date range."""
        params = {
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
        }
        return self._paginate("/v1/activity/sleep", params)

    def get_workouts(self, start: datetime, end: datetime) -> list[dict]:
        """Fetch workout records within a date range."""
        params = {
            "start": start.isoformat() + "Z",
            "end": end.isoformat() + "Z",
        }
        return self._paginate("/v1/activity/workout", params)

    def get_body_measurement(self) -> dict:
        """Fetch current body measurements."""
        resp = self.session.get("/v1/user/measurement/body")
        resp.raise_for_status()
        return resp.json()

    def revoke_token(self) -> None:
        """Revoke the current access token."""
        resp = self.session.delete("/v1/user/oauth/revoke")
        resp.raise_for_status()

    def _paginate(self, path: str, params: dict) -> list[dict]:
        """Handle cursor-based pagination."""
        results = []
        next_token = None
        while True:
            if next_token:
                params["nextToken"] = next_token
            resp = self.session.get(path, params=params)
            resp.raise_for_status()
            data = resp.json()
            results.extend(data.get("records", []))
            next_token = data.get("next_token")
            if not next_token:
                break
        return results
```

### 5.4 Data Transformation Layer

```python
# rivaflow/integrations/whoop/transformers.py (simplified)

def recovery_to_readiness(recovery: dict) -> dict:
    """Transform WHOOP recovery data to RivaFlow readiness fields."""
    score = recovery["score"]["recovery_score"]

    # Map 0-100% to 1-5 scale
    if score >= 90:
        sleep_val, energy_val = 5, 5
    elif score >= 67:
        sleep_val, energy_val = 4, 4
    elif score >= 50:
        sleep_val, energy_val = 3, 3
    elif score >= 34:
        sleep_val, energy_val = 2, 2
    else:
        sleep_val, energy_val = 1, 1

    return {
        "sleep": sleep_val,
        "energy": energy_val,
        "hrv_ms": recovery["score"].get("hrv_rmssd_milli"),
        "resting_hr": recovery["score"].get("resting_heart_rate"),
        "spo2": recovery["score"].get("spo2_percentage"),
        "whoop_recovery_score": score,
        "data_source": "whoop",
    }

def sleep_to_readiness(sleep: dict) -> dict:
    """Extract sleep quality metrics from WHOOP sleep data."""
    perf = sleep["score"].get("sleep_performance_percentage")
    return {
        "whoop_sleep_score": perf,
    }

def workout_to_session(workout: dict) -> dict:
    """Transform WHOOP workout to RivaFlow session WHOOP fields."""
    score = workout.get("score", {})
    kj = score.get("kilojoule", 0)
    return {
        "whoop_strain": score.get("strain"),
        "whoop_avg_hr": score.get("average_heart_rate"),
        "whoop_max_hr": score.get("max_heart_rate"),
        "whoop_calories": int(kj * 0.239006) if kj else None,
    }
```

### 5.5 Environment Variables

```bash
# .env additions for WHOOP integration
WHOOP_CLIENT_ID=your_whoop_client_id
WHOOP_CLIENT_SECRET=your_whoop_client_secret
WHOOP_REDIRECT_URI=https://rivaflow.onrender.com/api/whoop/callback
WHOOP_WEBHOOK_SECRET=your_webhook_verification_secret
ENABLE_WHOOP_INTEGRATION=true   # Already exists in settings.py
```

### 5.6 Settings Additions

```python
# Additions to rivaflow/core/settings.py

@property
def WHOOP_CLIENT_ID(self) -> str | None:
    """WHOOP OAuth client ID."""
    return os.getenv("WHOOP_CLIENT_ID")

@property
def WHOOP_CLIENT_SECRET(self) -> str | None:
    """WHOOP OAuth client secret."""
    return os.getenv("WHOOP_CLIENT_SECRET")

@property
def WHOOP_REDIRECT_URI(self) -> str:
    """WHOOP OAuth redirect URI."""
    return os.getenv(
        "WHOOP_REDIRECT_URI",
        f"{self.APP_BASE_URL}/api/whoop/callback"
    )

@property
def WHOOP_WEBHOOK_SECRET(self) -> str | None:
    """Secret for verifying WHOOP webhook signatures."""
    return os.getenv("WHOOP_WEBHOOK_SECRET")
```

---

## 6. User Experience

### 6.1 Settings Page -- WHOOP Connection

**State: Disconnected**
```
+---------------------------------------------------------------+
|  Integrations                                                 |
+---------------------------------------------------------------+
|                                                               |
|  WHOOP                                                        |
|  Connect your WHOOP strap to auto-populate readiness data     |
|  and track heart rate, HRV, and strain during training.       |
|                                                               |
|  [ Connect WHOOP ]                                            |
|                                                               |
+---------------------------------------------------------------+
```

**State: Connected**
```
+---------------------------------------------------------------+
|  Integrations                                                 |
+---------------------------------------------------------------+
|                                                               |
|  WHOOP                                         Connected      |
|  Last synced: 2026-02-07 08:15 UTC                            |
|                                                               |
|  Auto-populate readiness from WHOOP:   [ON]                   |
|  Sync workout strain data:             [ON]                   |
|  Sync body measurements:               [OFF]                  |
|                                                               |
|  [ Sync Now ]          [ Disconnect WHOOP ]                   |
|                                                               |
+---------------------------------------------------------------+
```

**State: Error / Token Expired**
```
+---------------------------------------------------------------+
|  Integrations                                                 |
+---------------------------------------------------------------+
|                                                               |
|  WHOOP                                    Reconnect Required  |
|  Your WHOOP connection has expired. Please reconnect to       |
|  continue syncing data.                                       |
|                                                               |
|  [ Reconnect WHOOP ]       [ Remove Connection ]             |
|                                                               |
+---------------------------------------------------------------+
```

### 6.2 Readiness Page -- WHOOP-Enhanced

When WHOOP data is available, the readiness check-in page changes behavior:

```
+---------------------------------------------------------------+
|  Daily Readiness Check-In           2026-02-07                |
+---------------------------------------------------------------+
|                                                               |
|  Data from WHOOP (auto-filled):                               |
|  +-----------------------------------------------------------+
|  |  Recovery: 84%  (Green)                                   |
|  |  HRV: 68 ms    Resting HR: 52 bpm    SpO2: 97%          |
|  |  Sleep Score: 85%   (7h 45m of 8h needed)                 |
|  +-----------------------------------------------------------+
|                                                               |
|  Sleep Quality     [====*=]  4/5  (from WHOOP)               |
|  Stress Level      [==*===]  3/5  (your input)               |
|  Soreness          [=*====]  2/5  (your input)               |
|  Energy Level      [====*=]  4/5  (from WHOOP)               |
|                                                               |
|  Hotspot / Pain    [________________________]                 |
|  Weight (kg)       [ 82.3 ] (from WHOOP)                     |
|                                                               |
|  Note: Sleep and Energy are pre-filled from your WHOOP       |
|  recovery score. You can adjust them if they don't match     |
|  how you feel.                                                |
|                                                               |
|  [ Save Readiness ]                                           |
|                                                               |
+---------------------------------------------------------------+
```

If the user overrides the WHOOP-derived values, `data_source` is set to `whoop+manual`.

### 6.3 Dashboard -- WHOOP Recovery Card

```
+---------------------------------------------------------------+
|  Dashboard                                                    |
+---------------------------------------------------------------+
|                                                               |
|  +---------------------------+  +---------------------------+ |
|  |  Today's Readiness  16/20 |  |  WHOOP Recovery     84%  | |
|  |  Label: Good              |  |  Zone: Green              | |
|  |  Sleep: 4  Stress: 3     |  |  HRV: 68 ms (avg: 62)    | |
|  |  Soreness: 2  Energy: 4  |  |  RHR: 52 bpm (avg: 54)   | |
|  +---------------------------+  +---------------------------+ |
|                                                               |
|  +---------------------------+  +---------------------------+ |
|  |  Weekly Training          |  |  WHOOP Strain (7d)        | |
|  |  Sessions: 4              |  |  Avg: 12.8 / 21          | |
|  |  Rolls: 22                |  |  Peak: 16.4 (Tue)        | |
|  |  Sub Ratio: 2.1           |  |  Total kCal: 4,280       | |
|  +---------------------------+  +---------------------------+ |
|                                                               |
+---------------------------------------------------------------+
```

### 6.4 Analytics -- WHOOP Trends

The existing `get_whoop_analytics()` method in `readiness_analytics.py` would be extended
to include the new recovery, sleep, and HRV trend data:

- **Recovery Score Over Time:** Line chart of daily recovery scores (7/30/90 day views)
- **HRV Trend:** Line chart with 7-day rolling average and personal baseline
- **Resting HR Trend:** Line chart showing cardiovascular fitness over time
- **Strain vs Recovery:** Scatter plot showing relationship between training load and
  next-day recovery
- **Sleep Performance:** Bar chart of nightly sleep scores with target line

---

## 7. Cost and Rate Limits

### 7.1 Pricing

| Item                        | Cost    | Notes                                         |
|-----------------------------|---------|-----------------------------------------------|
| WHOOP Developer API access  | Free    | No per-request or monthly charges              |
| WHOOP Developer Dashboard   | Free    | Up to 5 apps per developer account             |
| WHOOP membership (dev)      | ~$30/mo | Required to have a WHOOP device for testing    |
| RivaFlow infrastructure     | $0      | Webhook endpoint uses existing API server      |

**Total recurring cost to RivaFlow:** $0 (API access is free). The only cost is a WHOOP
membership for the developer account used during development and testing.

### 7.2 Rate Limits

| Limit                       | Value                | Window         |
|-----------------------------|----------------------|----------------|
| Requests per minute         | 100                  | 60 seconds     |
| Requests per day            | 10,000               | 86,400 seconds |

**Rate limit headers** are returned with every response:
- `RateLimit-Limit`: The limit closest to being hit
- `RateLimit-Remaining`: Remaining requests in the window
- `RateLimit-Reset`: Seconds until the window resets

**Exceeding limits** returns HTTP 429 (Too Many Requests).

### 7.3 Rate Limit Impact Analysis

Assuming RivaFlow has N connected WHOOP users:

**Webhook-driven sync (per event):**
- 1 API call per event (fetch full data)
- ~3 events per user per day (recovery + sleep + workout)
- N users = 3N calls/day

**Daily polling fallback (per user):**
- 4 API calls per user (recovery + sleep + workouts + body measurement)
- N users = 4N calls/day

**Combined worst case:** 7N calls/day

| Connected Users | Daily API Calls | Within Limit? | Headroom     |
|-----------------|-----------------|---------------|--------------|
| 100             | 700             | Yes           | 93% unused   |
| 500             | 3,500           | Yes           | 65% unused   |
| 1,000           | 7,000           | Yes           | 30% unused   |
| 1,428           | ~10,000         | Borderline    | 0% unused    |
| 2,000+          | 14,000+         | No            | Need partner |

**Conclusion:** The free tier comfortably supports up to ~1,000 connected WHOOP users.
Beyond that, RivaFlow would need to optimize (reduce polling frequency, rely more on
webhooks) or contact WHOOP about a partner arrangement for higher limits.

### 7.4 Partner Program

WHOOP does not publicly document a formal partner program with elevated rate limits.
For high-volume integrations, the recommended path is to contact WHOOP developer support
(support@whoop.com or via the Developer Dashboard) to discuss elevated access. Integrations
must be submitted for review before becoming fully available to WHOOP members.

---

## 8. Competitive Reference

### 8.1 Strava + WHOOP

- **Integration type:** Official, bidirectional
- **How it works:** WHOOP pushes completed activities (with strain, HR, calories) to Strava
  as workout entries. Sleep and recovery data are also visible on Strava.
- **User flow:** Connect in WHOOP app settings; activities auto-sync.
- **Relevance to RivaFlow:** Strava consumes WHOOP data to enrich activity records. RivaFlow
  would follow a similar pattern but also use recovery data for readiness scoring.

### 8.2 TrainingPeaks + WHOOP

- **Integration type:** Official, data push from WHOOP
- **How it works:** WHOOP pushes workout data to TrainingPeaks. TrainingPeaks uses strain and
  HR data to calculate TSS (Training Stress Score) equivalents.
- **User flow:** Enable in WHOOP app integrations page.
- **Relevance to RivaFlow:** TrainingPeaks demonstrates the value of using WHOOP strain data
  to quantify training load, analogous to how RivaFlow could correlate strain with BJJ
  performance metrics (submission ratios, etc.).

### 8.3 TrainHeroic + WHOOP

- **Integration type:** No direct integration exists
- **Current state:** TrainHeroic integrates with Apple Health and Zapier. Users have requested
  WHOOP integration (via UserVoice feedback forum) but it has not been built.
- **Relevance to RivaFlow:** This is a gap in the market. A strength/combat sport-focused app
  with native WHOOP integration would differentiate RivaFlow from TrainHeroic.

### 8.4 Competitive Summary

| App            | WHOOP Integration | Recovery Data | Auto-Readiness | BJJ-Specific |
|----------------|-------------------|---------------|----------------|--------------|
| Strava         | Yes (official)    | Display only  | No             | No           |
| TrainingPeaks  | Yes (official)    | Limited       | No             | No           |
| TrainHeroic    | No                | N/A           | No             | No           |
| WHOOP App      | Native            | Full          | Yes (own model)| No           |
| **RivaFlow**   | **Proposed**      | **Full**      | **Yes**        | **Yes**      |

**Key differentiator:** RivaFlow would be the only BJJ-specific training tracker with native
WHOOP integration that uses recovery data to drive sport-specific readiness recommendations
(e.g., "Recovery is 45% -- consider drilling instead of live rolling today").

---

## 9. Risks and Mitigations

| # | Risk                                    | Likelihood | Impact | Mitigation                                        |
|---|----------------------------------------|------------|--------|---------------------------------------------------|
| 1 | WHOOP changes API without notice       | Low        | High   | Pin to v1, monitor changelog, build adapter layer |
| 2 | WHOOP rate limits become restrictive   | Low        | Medium | Webhook-first architecture minimizes polling      |
| 3 | Token refresh failures in production   | Medium     | Medium | Retry logic, user notification, auto-reconnect UI |
| 4 | WHOOP rejects integration review       | Low        | High   | Follow API terms, minimal scope, good UX          |
| 5 | Low user adoption (few WHOOP owners)   | Medium     | Low    | Feature is additive; no cost if unused             |
| 6 | Data privacy concerns (health data)    | Medium     | High   | Encrypt tokens, minimal data retention, GDPR flow |
| 7 | Webhook endpoint downtime misses events| Medium     | Low    | Daily polling reconciliation catches gaps          |
| 8 | WHOOP deprecates v1 before we migrate  | Low        | Medium | Migration guide available; v2 is similar           |

---

## 10. Recommendation

### Verdict: BUILD (Phase 1 in Q2 2026, Phase 2 in Q3 2026)

**Justification:**

1. **Technical feasibility is high.** RivaFlow already has WHOOP fields in the sessions table
   (migration 011), a `get_whoop_analytics()` method, and an `ENABLE_WHOOP_INTEGRATION` feature
   flag in `settings.py`. The foundation is laid; the integration completes it.

2. **API is free and well-documented.** Zero incremental cost to RivaFlow. The WHOOP Developer
   Platform is mature (v2 launched July 2025) with webhooks, OAuth 2.0, and reasonable rate
   limits.

3. **Strong product-market fit.** BJJ practitioners are disproportionately likely to own
   wearables for recovery optimization. WHOOP is especially popular in combat sports
   (numerous UFC fighters and BJJ competitors use WHOOP publicly). Automated readiness
   scoring is a natural extension of RivaFlow's existing check-in model.

4. **Competitive differentiation.** No existing BJJ tracker offers native WHOOP integration.
   TrainHeroic, the closest competitor in strength/combat training, lacks this integration
   entirely.

5. **Low risk.** The feature is entirely additive. Users without WHOOP continue using manual
   readiness check-ins with zero impact. The integration can be gated behind the existing
   `ENABLE_WHOOP_INTEGRATION` feature flag.

### Phased Approach

**Phase 1 (MVP):** OAuth flow, token storage, daily polling sync, readiness auto-population,
basic WHOOP recovery card on dashboard. No webhooks. Target: 4 weeks.

**Phase 2 (Enhanced):** Webhook support, real-time sync, workout strain auto-matching to
sessions, WHOOP trend analytics, body measurement sync. Target: 3 weeks.

**Phase 3 (Advanced, optional):** Training recommendations based on WHOOP recovery
("Your recovery is 38% -- consider light drilling or rest today"), HRV trend alerts,
integration with Grapple AI coach for recovery-aware suggestions. Target: 2 weeks.

### Alternative Considered: Apple Health / HealthKit Bridge

Instead of a direct WHOOP integration, RivaFlow could read from Apple Health, which WHOOP
already syncs to. This was rejected because:
- Requires a native iOS app (RivaFlow is currently web-based)
- Apple Health data is less granular (no recovery score, limited HRV access)
- Would not provide the differentiated "WHOOP-native" user experience

---

## 11. Effort Estimate

### Phase 1: MVP (4 weeks, 1 developer)

| Task                                          | Estimate | Priority |
|-----------------------------------------------|----------|----------|
| WHOOP Developer Dashboard setup               | 0.5 day  | P0       |
| Database migrations (tokens + readiness cols) | 1 day    | P0       |
| OAuth flow (connect/callback/disconnect)      | 2 days   | P0       |
| Token manager (encrypt, store, refresh)       | 1.5 days | P0       |
| WHOOP API client (recovery, sleep, workouts)  | 2 days   | P0       |
| Data transformation layer                     | 1.5 days | P0       |
| Daily sync job (polling)                      | 1.5 days | P0       |
| API routes (/whoop/connect, /status, etc.)    | 1 day    | P0       |
| Frontend: Settings page integration UI        | 2 days   | P0       |
| Frontend: Readiness page WHOOP auto-fill      | 1.5 days | P0       |
| Frontend: Dashboard WHOOP recovery card       | 1 day    | P0       |
| Testing (unit + integration + manual)         | 3 days   | P0       |
| Documentation                                 | 0.5 day  | P1       |
| **Total Phase 1**                             | **19 days (~4 weeks)** |  |

### Phase 2: Enhanced (3 weeks, 1 developer)

| Task                                          | Estimate | Priority |
|-----------------------------------------------|----------|----------|
| Webhook endpoint + event routing              | 2 days   | P0       |
| Webhook signature verification                | 0.5 day  | P0       |
| Real-time sync on webhook events              | 1.5 days | P0       |
| Workout-to-session auto-matching              | 2 days   | P1       |
| WHOOP trend analytics (HRV, RHR, recovery)    | 3 days   | P1       |
| Frontend: Analytics WHOOP trends page         | 2 days   | P1       |
| Body measurement sync                         | 1 day    | P2       |
| Error handling hardening + retry logic        | 1.5 days | P0       |
| Testing                                       | 2 days   | P0       |
| **Total Phase 2**                             | **15.5 days (~3 weeks)** | |

### Phase 3: Advanced (2 weeks, 1 developer)

| Task                                          | Estimate | Priority |
|-----------------------------------------------|----------|----------|
| Recovery-based training recommendations       | 3 days   | P1       |
| HRV trend alerts (significant drops)          | 1.5 days | P2       |
| Grapple AI integration (recovery context)     | 2 days   | P2       |
| Overtraining detection algorithm              | 2 days   | P2       |
| Testing + polish                              | 1.5 days | P0       |
| **Total Phase 3**                             | **10 days (~2 weeks)** |  |

### Total Effort

| Phase   | Duration   | Developer Days | Cumulative |
|---------|------------|----------------|------------|
| Phase 1 | 4 weeks    | 19 days        | 19 days    |
| Phase 2 | 3 weeks    | 15.5 days      | 34.5 days  |
| Phase 3 | 2 weeks    | 10 days        | 44.5 days  |
| **All** | **9 weeks**| **44.5 days**  | --         |

---

## 12. Appendix

### A. WHOOP Developer Resources

- WHOOP Developer Portal: https://developer.whoop.com
- API Documentation: https://developer.whoop.com/api
- OAuth 2.0 Guide: https://developer.whoop.com/docs/developing/oauth
- Webhooks: https://developer.whoop.com/docs/developing/webhooks
- Rate Limiting: https://developer.whoop.com/docs/developing/rate-limiting
- API Changelog: https://developer.whoop.com/docs/api-changelog
- v1 to v2 Migration: https://developer.whoop.com/docs/developing/v1-v2-migration
- API Terms of Use: https://developer.whoop.com/api-terms-of-use

### B. Existing RivaFlow WHOOP Touchpoints

The following files already reference WHOOP and would be modified or extended:

| File                                              | Current State                          |
|---------------------------------------------------|----------------------------------------|
| `rivaflow/core/settings.py`                       | `ENABLE_WHOOP_INTEGRATION` flag exists |
| `rivaflow/core/models.py`                         | `whoop_strain/calories/hr` on Session  |
| `rivaflow/db/migrations/011_add_whoop_stats.sql`  | Session-level WHOOP columns exist      |
| `rivaflow/core/services/readiness_analytics.py`   | `get_whoop_analytics()` method exists  |
| `rivaflow/db/repositories/session_repo.py`        | Queries WHOOP session fields           |
| `rivaflow/api/routes/analytics.py`                | Exposes WHOOP analytics endpoint       |

### C. WHOOP Recovery Score Methodology

WHOOP calculates Recovery using:
1. **Heart Rate Variability (HRV)** -- Primary input, measured during deepest sleep via
   RMSSD (root mean square of successive R-R interval differences)
2. **Resting Heart Rate (RHR)** -- Secondary input, lower = better recovered
3. **Sleep Performance** -- How much sleep obtained vs. how much the body needed
4. **Respiratory Rate** -- Deviations from baseline may indicate illness or stress
5. **SpO2** -- Blood oxygen saturation
6. **Skin Temperature** -- Deviations from baseline

The algorithm is proprietary, but HRV is the dominant factor. RHR and sleep provide
largely redundant information to HRV but serve as confirmation signals.

### D. WHOOP Sport ID Mapping for BJJ

| Sport ID | WHOOP Activity Name    | RivaFlow ClassType     |
|----------|------------------------|------------------------|
| 84       | Martial Arts           | `gi`, `no-gi`, `mma`   |
| 87       | Brazilian Jiu-Jitsu    | `gi`, `no-gi`          |
| 86       | Wrestling              | `wrestling`            |
| 82       | Judo                   | `judo`                 |
| 41       | Yoga                   | `yoga`                 |
| 1        | Running                | `cardio`               |
| 0        | Strength Training      | `s&c`                  |
| 71       | Stretching             | `mobility`, `rehab`    |

---

*End of scoping document.*
