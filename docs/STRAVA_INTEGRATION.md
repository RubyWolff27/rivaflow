# Strava Integration

**Status:** Implemented
**Replaces:** the Mac-side Garmin push job (`RivaFlowGarminPush`)

---

## Why this exists

RivaFlow's per-session biometrics used to arrive from a job running on a Mac, which
read a Garmin and POSTed to `/api/v1/garmin/daily`. That design had a single point of
failure: the device and the machine. When the Garmin was lost on **2026-06-30**, the
job had nothing to read and sessions stopped appearing.

Strava fixes the shape of the problem, not just the instance. Wahoo hardware — and
Coros, Suunto, Garmin, and most other trackers — auto-uploads to Strava. RivaFlow now
**pulls from Strava's API server-side**, so capture no longer depends on any machine
you personally own being awake.

### Why not Google

Wahoo can sync to Google, but Google cannot feed RivaFlow. The Google Fit REST API has
been closed to new signups since May 2024 and is in end-of-service through late 2026,
and its replacement — Health Connect — is an **Android on-device** data store with no
cloud API for a server to read. Google can remain your phone's aggregator; it cannot be
RivaFlow's source.

### Why not Wahoo directly

Wahoo does publish a Cloud API (OAuth 2.0, `api.wahooligan.com`), and it is a reasonable
future addition. It is gated behind an application and approval process, so it cannot
repair a historical gap today. Strava's API is self-serve and already holds the history.

---

## Setup

### 1. Create the Strava app

Go to <https://www.strava.com/settings/api> and create an application.

- **Authorization Callback Domain** — your API host, with no scheme and no path:
  `api.rivaflow.app` (production) or `localhost` (development).
- Note the **Client ID** and **Client Secret**.

New Strava apps start in *single-player mode*: only your own account can authenticate
with them. That is exactly what is needed here, and requires no review.

### 2. Configure the server

```bash
ENABLE_STRAVA_INTEGRATION=true
STRAVA_CLIENT_ID=<client id>
STRAVA_CLIENT_SECRET=<client secret>
STRAVA_REDIRECT_URI=https://api.rivaflow.app/api/v1/integrations/strava/callback
STRAVA_CONNECT_REDIRECT=https://rivaflow.app/profile

# Generate with:
#   python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
TOKEN_ENCRYPTION_KEY=<fernet key>
```

If a deployment already has `WHOOP_ENCRYPTION_KEY` set, `TOKEN_ENCRYPTION_KEY` can be
omitted — it falls back to that value. Do not set both to *different* keys.

### 3. Connect

Profile → **Connected Devices** → **Connect Strava**.

> **Grant the private-activity permission.** The consent screen offers *"View data about
> your private activities"*. Without it, anything marked private on Strava is invisible
> to the API and silently will not import. The Connected Devices card warns if the
> connection is missing this scope.

### 4. Backfill a gap

Profile → Connected Devices → Strava → **Backfill**, then pick a date range.

The backfill is idempotent. It upserts on Strava's activity id and skips activities
already linked to a session, so re-running the same range repairs a partial import
rather than duplicating it.

---

## How activities become sessions

Auto-created sessions are written with `source='strava'` and **`needs_review=true`** —
they appear for confirmation rather than passing themselves off as hand-logged data.

**Class type.** Name heuristics run first and beat `sport_type`, because BJJ has no
Strava sport type and is almost always logged as a generic "Workout" — the activity name
is the only mat-time signal:

| Activity name contains | Imports as |
|---|---|
| `no-gi`, `nogi` | `no-gi` |
| `open mat` | `open-mat` |
| `comp`, `tournament`, `ibjjf`, `adcc` | `competition` |
| `wrestl…` | `wrestling` |
| `judo` | `judo` |
| `drill…` | `drilling` |
| `gi` (whole word) | `gi` |
| `bjj`, `jiu-jitsu`, `grappling`, `rolls` | the user's most-used class type |

Unmatched names fall back to `sport_type` (`WeightTraining`/`Crossfit` → `s&c`,
`Run`/`Ride`/`Swim` → `cardio`, `Yoga` → `yoga`).

**Filtering.** Activities under 20 minutes, and walks/hikes/golf, are cached but never
auto-created — they would otherwise bury real training.

**Intensity** is derived from Strava's Relative Effort where present, otherwise from the
average/max heart-rate ratio, defaulting to 3.

**Biometrics** land on dedicated `strava_*` session columns and render in a Strava panel
on the session detail page. They deliberately do not reuse `garmin_*` or `whoop_*`,
which would misattribute the data in the UI.

---

## Rate limits

Strava allows 100 non-upload requests per 15 minutes and 1,000 per day.

Heart rate and calories are **not** on the activity list payload — they require a detail
call per activity. A one-month backfill of ~40 activities costs 1 list call plus ~40
detail calls, comfortably inside the limit. `_ACTIVITY_DETAIL_BUDGET` (90) caps the
fan-out for a pathological range; when it is hit the sync response carries
`detail_budget_exhausted` and a warning telling you to re-run a narrower range, rather
than silently returning partial data.

Detail calls are skipped for activities already enriched, so re-running a backfill is
cheap.

---

## Endpoints

All under `/api/v1/integrations/strava`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/status` | Connection state for the settings screen |
| GET | `/authorize` | Build the consent URL |
| GET | `/callback` | OAuth redirect target (unauthenticated by design; bound by single-use `state`) |
| POST | `/sync?days=N` | Pull the last N days |
| POST | `/backfill` | Pull an explicit `start_date`/`end_date` range |
| GET | `/importable` | Unlinked activities with suggested class type |
| POST | `/import` | Turn one cached activity into a session |
| POST | `/dismiss` | Hide an activity from the import list |
| POST | `/auto-create-sessions` | Toggle auto-creation |
| DELETE | `` | Disconnect (keeps imported sessions and cache) |

---

## Operational notes

- **Refresh tokens rotate.** Strava issues a new refresh token on every refresh and
  invalidates the old one. `StravaRepository.update_tokens` persists the rotation; losing
  it bricks the connection on the next sync.
- **Tokens are Fernet-encrypted at rest.** The repository layer only ever handles
  ciphertext; decryption lives in the service.
- **Disconnect keeps history.** Tokens are cleared but the activity cache and imported
  sessions remain, so reconnecting does not re-import everything.

---

## Schema

- `118_strava_integration` — `strava_connections`, `strava_activity_cache`,
  `strava_oauth_states`
- `119_strava_session_biometrics` — `strava_*` columns on `sessions`, plus a partial
  unique index on `(user_id, strava_activity_id)` that makes duplicate imports
  impossible at the database level
