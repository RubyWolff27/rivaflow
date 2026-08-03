"""Strava integration — OAuth, activity sync, and activity→session mapping.

Why Strava: RivaFlow's biometrics used to arrive from a Mac-side Garmin push job
(RivaFlowGarminPush). When the Garmin went, so did the job, and sessions stopped
on 2026-06-30. Wahoo hardware auto-uploads to Strava, and Strava's API is
self-serve, so it becomes the replacement capture path — the server pulls, rather
than depending on a machine on someone's desk.

Two things worth knowing about Strava's API before changing this module:

1. The list endpoint (``/athlete/activities``) does NOT reliably carry heart rate
   or calories — those live on the detail endpoint (``/activities/{id}``). The
   sync therefore does a per-activity detail fetch, which is the whole point for
   BJJ sessions. ``_ACTIVITY_DETAIL_BUDGET`` bounds that fan-out.
2. Refresh tokens ROTATE. Every refresh returns a new refresh token and the old
   one dies. Failing to persist it bricks the connection on the next sync.
"""

from __future__ import annotations

import logging
import re
from datetime import UTC, date, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx

from rivaflow.core.exceptions import ExternalServiceError, ValidationError
from rivaflow.core.settings import settings
from rivaflow.core.utils.encryption import decrypt_token, encrypt_token
from rivaflow.db.database import convert_query
from rivaflow.db.repositories.base_repository import BaseRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.strava_repo import StravaRepository

logger = logging.getLogger(__name__)

STRAVA_AUTHORIZE_URL = "https://www.strava.com/oauth/authorize"
STRAVA_TOKEN_URL = "https://www.strava.com/oauth/token"
STRAVA_API_BASE = "https://www.strava.com/api/v3"

# activity:read_all is required — activity:read alone hides activities the athlete
# has marked private, which for a gym/BJJ session is the common case.
STRAVA_SCOPES = "read,activity:read_all"

# Refresh a little before actual expiry so a long sync cannot expire mid-flight.
_TOKEN_EXPIRY_SKEW_SEC = 300

_HTTP_TIMEOUT = httpx.Timeout(20.0, connect=10.0)

# Strava allows 100 non-upload requests per 15 minutes. A month-long backfill of
# ~40 activities costs 1 list call + 40 detail calls, comfortably inside that, but
# the cap stops a pathological range from burning the whole quota in one request.
_ACTIVITY_DETAIL_BUDGET = 90

_MAX_PAGE_SIZE = 200


class StravaNotConnectedError(ValidationError):
    """Raised when an operation needs a Strava connection the user does not have."""

    default_message = "Strava is not connected"


class StravaAuthExpiredError(ExternalServiceError):
    """Raised when the stored refresh token is no longer accepted by Strava."""

    default_message = "Strava authorisation expired — reconnect required"


# ---------------------------------------------------------------------------
# Activity classification
# ---------------------------------------------------------------------------

# Strava sport_type → RivaFlow class_type. Only covers what a grappler plausibly
# logs; anything unmatched falls through to the name heuristics and then to the
# cardio default.
_SPORT_TYPE_MAP: dict[str, str] = {
    "WeightTraining": "s&c",
    "Crossfit": "s&c",
    "HighIntensityIntervalTraining": "s&c",
    "Workout": "s&c",
    "Yoga": "yoga",
    "Pilates": "mobility",
    "Run": "cardio",
    "TrailRun": "cardio",
    "VirtualRun": "cardio",
    "Ride": "cardio",
    "VirtualRide": "cardio",
    "GravelRide": "cardio",
    "MountainBikeRide": "cardio",
    "EBikeRide": "cardio",
    "EMountainBikeRide": "cardio",
    "Swim": "cardio",
    "Rowing": "cardio",
    "VirtualRow": "cardio",
    "Elliptical": "cardio",
    "StairStepper": "cardio",
    "Walk": "cardio",
    "Hike": "cardio",
}

# Name heuristics, highest specificity first. These beat sport_type because BJJ has
# no Strava sport type — it is almost always logged as a generic "Workout", so the
# activity name is the only signal that it was mat time.
# Word-boundary anchored: a bare \bgi\b must not fire on "begin" or "Gippsland".
_NAME_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\b(no[\s\-_]?gi|nogi)\b", re.I), "no-gi"),
    (re.compile(r"\bopen[\s\-_]?mat\b", re.I), "open-mat"),
    (re.compile(r"\b(comp(etition)?|tournament|ibjjf|adcc)\b", re.I), "competition"),
    (re.compile(r"\bwrestl\w*\b", re.I), "wrestling"),
    (re.compile(r"\bjudo\b", re.I), "judo"),
    (re.compile(r"\bdrill\w*\b", re.I), "drilling"),
    (re.compile(r"\b(mobility|stretch\w*|recovery\s+flow)\b", re.I), "mobility"),
    (re.compile(r"\b(rehab|physio\w*)\b", re.I), "physio"),
    (re.compile(r"\byoga\b", re.I), "yoga"),
    (re.compile(r"\bgi\b", re.I), "gi"),
    # Generic grappling terms resolve to the user's usual class type (see
    # _default_bjj_class_type) rather than guessing gi vs no-gi.
    (re.compile(r"\b(bjj|jiu[\s\-_]?jitsu|jits|grappl\w*|roll\w*|mat)\b", re.I), ""),
    (re.compile(r"\b(s&c|strength|lift\w*|gym)\b", re.I), "s&c"),
]

# Activity names/types that are almost never a training session worth importing.
# These still get cached (so they can be matched manually) but are not auto-created.
_NON_TRAINING_SPORT_TYPES = frozenset({"Walk", "Hike", "Golf", "Sail", "Skateboard"})

# Below this, an activity is a commute or a stroll, not a session.
_MIN_SESSION_MINUTES = 20


def classify_activity(activity: dict, default_bjj_class_type: str = "no-gi") -> str:
    """Map a cached Strava activity to a RivaFlow class_type.

    Name heuristics win over sport_type because BJJ has no Strava sport type and
    is logged as a generic "Workout"; the name is the only mat-time signal.
    """
    name = activity.get("name") or ""
    for pattern, class_type in _NAME_RULES:
        if pattern.search(name):
            # Empty target means "grappling, but unspecified" — defer to the
            # user's own most-common class type instead of guessing.
            return class_type or default_bjj_class_type

    sport = activity.get("sport_type") or activity.get("activity_type") or ""
    return _SPORT_TYPE_MAP.get(sport, "cardio")


def is_importable(activity: dict) -> bool:
    """Whether a cached activity is worth auto-creating a session for.

    Filters out the noise that would otherwise bury real training: commutes,
    walks, and anything too short to be a class.
    """
    if activity.get("session_id") is not None or activity.get("dismissed"):
        return False

    sport = activity.get("sport_type") or activity.get("activity_type") or ""
    if sport in _NON_TRAINING_SPORT_TYPES:
        return False

    seconds = activity.get("elapsed_time_sec") or activity.get("moving_time_sec") or 0
    return (seconds / 60.0) >= _MIN_SESSION_MINUTES


def derive_intensity(activity: dict) -> int:
    """Best-effort 1–5 intensity from Strava's Relative Effort, else heart rate.

    Deliberately conservative — the session is flagged needs_review, so a wrong
    guess costs the user one dropdown, whereas an over-confident 5 skews ACWR.
    """
    suffer = activity.get("suffer_score")
    if suffer is not None:
        for threshold, value in ((20, 2), (40, 3), (75, 4)):
            if suffer < threshold:
                return value
        return 5

    avg_hr = activity.get("avg_heart_rate")
    max_hr = activity.get("max_heart_rate")
    if avg_hr and max_hr and max_hr > 0:
        ratio = avg_hr / max_hr
        for threshold, value in ((0.60, 2), (0.72, 3), (0.85, 4)):
            if ratio < threshold:
                return value
        return 5

    return 3


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


class StravaClient:
    """Thin HTTP wrapper around the Strava v3 API."""

    @staticmethod
    def _post_token(payload: dict) -> dict:
        try:
            with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
                response = client.post(STRAVA_TOKEN_URL, data=payload)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Strava token request failed: {exc}") from exc

        if response.status_code in (400, 401):
            # Strava returns 400 for an invalid/revoked refresh token.
            raise StravaAuthExpiredError()
        if response.status_code >= 400:
            raise ExternalServiceError(
                f"Strava token request failed ({response.status_code})"
            )
        return response.json()

    @classmethod
    def exchange_code(cls, code: str) -> dict:
        """Trade an authorization code for the initial token pair."""
        return cls._post_token(
            {
                "client_id": settings.STRAVA_CLIENT_ID,
                "client_secret": settings.STRAVA_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
            }
        )

    @classmethod
    def refresh(cls, refresh_token: str) -> dict:
        """Exchange a refresh token for a new access token (and a new refresh token)."""
        return cls._post_token(
            {
                "client_id": settings.STRAVA_CLIENT_ID,
                "client_secret": settings.STRAVA_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }
        )

    @staticmethod
    def _get(access_token: str, path: str, params: dict | None = None) -> Any:
        try:
            with httpx.Client(timeout=_HTTP_TIMEOUT) as client:
                response = client.get(
                    f"{STRAVA_API_BASE}{path}",
                    params=params or {},
                    headers={"Authorization": f"Bearer {access_token}"},
                )
        except httpx.HTTPError as exc:
            raise ExternalServiceError(f"Strava API request failed: {exc}") from exc

        if response.status_code == 401:
            raise StravaAuthExpiredError()
        if response.status_code == 429:
            raise ExternalServiceError(
                "Strava rate limit reached — try again in 15 minutes"
            )
        if response.status_code >= 400:
            raise ExternalServiceError(f"Strava API error ({response.status_code})")
        return response.json()

    @classmethod
    def list_activities(
        cls,
        access_token: str,
        after: datetime | None = None,
        before: datetime | None = None,
        page: int = 1,
        per_page: int = _MAX_PAGE_SIZE,
    ) -> list[dict]:
        """One page of the athlete's activities. `after`/`before` are epoch seconds."""
        params: dict[str, Any] = {
            "page": page,
            "per_page": min(per_page, _MAX_PAGE_SIZE),
        }
        if after is not None:
            params["after"] = int(after.timestamp())
        if before is not None:
            params["before"] = int(before.timestamp())
        result = cls._get(access_token, "/athlete/activities", params)
        return result if isinstance(result, list) else []

    @classmethod
    def get_activity(cls, access_token: str, activity_id: str) -> dict:
        """Detailed activity — the only place heart rate and calories are reliable."""
        result = cls._get(access_token, f"/activities/{activity_id}")
        return result if isinstance(result, dict) else {}


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


def _parse_dt(value: Any) -> datetime | None:
    """Parse Strava's ISO-8601 timestamps ('2026-07-14T20:30:00Z')."""
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None


def _as_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def _as_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


class StravaService:
    """OAuth lifecycle, activity sync, and session creation for Strava."""

    # -- OAuth ---------------------------------------------------------

    @staticmethod
    def _require_configured() -> None:
        if not settings.STRAVA_CLIENT_ID or not settings.STRAVA_CLIENT_SECRET:
            raise ValidationError(
                "Strava is not configured on this server — "
                "set STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET"
            )

    @classmethod
    def build_authorize_url(cls, user_id: int) -> str:
        """Authorization URL for the consent redirect, carrying a one-shot state."""
        cls._require_configured()
        state = StravaRepository.create_state(user_id)
        query = urlencode(
            {
                "client_id": settings.STRAVA_CLIENT_ID,
                "redirect_uri": settings.STRAVA_REDIRECT_URI,
                "response_type": "code",
                "approval_prompt": "auto",
                "scope": STRAVA_SCOPES,
                "state": state,
            }
        )
        return f"{STRAVA_AUTHORIZE_URL}?{query}"

    @classmethod
    def complete_oauth(cls, state: str, code: str, scope: str | None = None) -> int:
        """Redeem the callback, store tokens, and return the connected user_id."""
        cls._require_configured()
        user_id = StravaRepository.consume_state(state)
        if user_id is None:
            raise ValidationError("Invalid or expired OAuth state")

        payload = StravaClient.exchange_code(code)
        granted = scope or payload.get("scope") or STRAVA_SCOPES

        # activity:read_all is what makes private activities visible. Without it a
        # backfill silently returns a fraction of the real training history, which
        # is worse than failing loudly.
        if "activity:read_all" not in granted:
            logger.warning(
                "Strava connected for user %s without activity:read_all — "
                "private activities will be invisible",
                user_id,
            )

        athlete = payload.get("athlete") or {}
        StravaRepository.upsert_connection(
            user_id=user_id,
            athlete_id=str(athlete.get("id")) if athlete.get("id") else None,
            access_token_encrypted=encrypt_token(payload["access_token"]),
            refresh_token_encrypted=encrypt_token(payload["refresh_token"]),
            token_expires_at=datetime.fromtimestamp(payload["expires_at"], tz=UTC),
            scopes=granted,
        )
        logger.info(
            "Strava connected — user_id=%s athlete=%s", user_id, athlete.get("id")
        )
        return user_id

    @classmethod
    def get_access_token(cls, user_id: int) -> str:
        """A valid access token, refreshing (and persisting the rotation) if needed."""
        connection = StravaRepository.get_connection_row(user_id)
        if not connection:
            raise StravaNotConnectedError()

        expires_at = connection["token_expires_at"]
        if isinstance(expires_at, str):
            expires_at = datetime.fromisoformat(expires_at)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)

        if expires_at > datetime.now(UTC) + timedelta(seconds=_TOKEN_EXPIRY_SKEW_SEC):
            return decrypt_token(connection["access_token_encrypted"])

        payload = StravaClient.refresh(
            decrypt_token(connection["refresh_token_encrypted"])
        )
        # Strava rotates the refresh token on every refresh — persist it or the
        # next sync fails with an unrecoverable auth error.
        StravaRepository.update_tokens(
            user_id=user_id,
            access_token_encrypted=encrypt_token(payload["access_token"]),
            refresh_token_encrypted=encrypt_token(payload["refresh_token"]),
            token_expires_at=datetime.fromtimestamp(payload["expires_at"], tz=UTC),
        )
        return payload["access_token"]

    @staticmethod
    def disconnect(user_id: int) -> bool:
        """Drop the stored tokens. Imported sessions and cache rows are kept."""
        return StravaRepository.disconnect(user_id)

    @staticmethod
    def get_status(user_id: int) -> dict:
        """Connection state for the settings screen."""
        connection = StravaRepository.get_connection_row(user_id)
        if not connection:
            return {
                "connected": False,
                "configured": bool(settings.STRAVA_CLIENT_ID),
                "athlete_id": None,
                "last_synced_at": None,
                "auto_create_sessions": False,
                "cached_activities": 0,
                "scopes": None,
                "has_private_scope": False,
            }
        scopes = connection.get("scopes") or ""
        return {
            "connected": True,
            "configured": bool(settings.STRAVA_CLIENT_ID),
            "athlete_id": connection.get("athlete_id"),
            "last_synced_at": connection.get("last_synced_at"),
            "auto_create_sessions": bool(connection.get("auto_create_sessions")),
            "cached_activities": StravaRepository.count_for_user(user_id),
            "scopes": scopes,
            "has_private_scope": "activity:read_all" in scopes,
        }

    # -- Mapping -------------------------------------------------------

    @staticmethod
    def map_activity_fields(summary: dict, detail: dict | None = None) -> dict:
        """Flatten a Strava activity (summary + optional detail) to cache columns.

        Detail wins where present: heart rate and calories are absent or unreliable
        on the summary payload.
        """
        merged: dict[str, Any] = {**summary, **(detail or {})}
        started = _parse_dt(merged.get("start_date"))
        return {
            "external_id": merged.get("external_id"),
            "name": merged.get("name"),
            "activity_type": merged.get("type"),
            "sport_type": merged.get("sport_type") or merged.get("type"),
            "start_time": started,
            "start_time_local": _parse_dt(merged.get("start_date_local")),
            "timezone": merged.get("timezone"),
            "elapsed_time_sec": _as_int(merged.get("elapsed_time")),
            "moving_time_sec": _as_int(merged.get("moving_time")),
            "distance_m": _as_float(merged.get("distance")),
            "avg_heart_rate": _as_int(merged.get("average_heartrate")),
            "max_heart_rate": _as_int(merged.get("max_heartrate")),
            "has_heartrate": bool(merged.get("has_heartrate")),
            "calories": _as_int(merged.get("calories")),
            "kilojoules": _as_float(merged.get("kilojoules")),
            "suffer_score": _as_float(merged.get("suffer_score")),
            "device_name": merged.get("device_name"),
            "trainer": bool(merged.get("trainer")),
            "manual": bool(merged.get("manual")),
            "detail_fetched": detail is not None,
            "raw_data": merged,
        }

    @staticmethod
    def _default_bjj_class_type(user_id: int) -> str:
        """The user's most-used grappling class type, for unlabelled mat time.

        Better than hard-coding gi or no-gi: it matches whatever they actually
        train. Falls back to no-gi for a brand-new account with no history.
        """
        row = BaseRepository._fetchone(
            convert_query(
                "SELECT class_type, COUNT(*) AS n FROM sessions "
                "WHERE user_id = ? AND class_type IN ('gi', 'no-gi') "
                "GROUP BY class_type ORDER BY n DESC LIMIT 1"
            ),
            (user_id,),
        )
        return row["class_type"] if row else "no-gi"

    @staticmethod
    def _default_gym_name(user_id: int) -> str:
        """The user's most recent gym — sessions require a non-empty gym_name."""
        row = BaseRepository._fetchone(
            convert_query(
                "SELECT gym_name FROM sessions WHERE user_id = ? AND gym_name <> '' "
                "ORDER BY session_date DESC LIMIT 1"
            ),
            (user_id,),
        )
        return (row or {}).get("gym_name") or "Unknown"

    # -- Sync ----------------------------------------------------------

    @staticmethod
    def _fetch_all_pages(
        access_token: str, after: datetime, before: datetime
    ) -> list[dict]:
        """Every activity summary in the window, following pagination."""
        summaries: list[dict] = []
        page = 1
        while True:
            batch = StravaClient.list_activities(
                access_token, after=after, before=before, page=page
            )
            if not batch:
                break
            summaries.extend(batch)
            if len(batch) < _MAX_PAGE_SIZE:
                break
            page += 1
        return summaries

    @staticmethod
    def _maybe_fetch_detail(
        user_id: int, access_token: str, activity_id: str, budget_left: int
    ) -> tuple[dict | None, int]:
        """Fetch the detail payload if it can still tell us something new.

        Returns ``(detail, calls_spent)``. Skips the call when the activity was
        already enriched, and swallows a per-activity failure so one unreadable
        activity cannot abort a month-long backfill.
        """
        existing = StravaRepository.get_activity_by_strava_id(user_id, activity_id)
        if existing and existing.get("detail_fetched"):
            return None, 0
        if budget_left <= 0:
            return None, 0
        try:
            return StravaClient.get_activity(access_token, activity_id), 1
        except ExternalServiceError as exc:
            logger.warning(
                "Strava detail fetch failed for activity %s: %s", activity_id, exc
            )
            return None, 1

    @classmethod
    def _store_activity(
        cls,
        user_id: int,
        activity_id: str,
        summary: dict,
        detail: dict | None,
        auto_create: bool,
        tally: dict,
    ) -> None:
        """Cache one activity and, when enabled, create its session. Mutates tally."""
        fields = cls.map_activity_fields(summary, detail)
        if fields["start_time"] is None:
            # start_time is NOT NULL — skip rather than abort the backfill.
            logger.warning(
                "Strava activity %s has no parsable start_date — skipped", activity_id
            )
            tally["skipped"] += 1
            return

        cache_id, was_created = StravaRepository.upsert_activity(
            user_id, activity_id, **fields
        )
        tally["created" if was_created else "updated"] += 1

        if auto_create:
            cached = StravaRepository.get_activity(user_id, cache_id)
            if cached and cls._auto_create_session(user_id, cached):
                tally["sessions_created"] += 1

    @classmethod
    def sync(
        cls,
        user_id: int,
        after: datetime | None = None,
        before: datetime | None = None,
        days: int | None = None,
        auto_create: bool | None = None,
    ) -> dict:
        """Pull activities in a window, cache them, and optionally create sessions.

        Idempotent: the cache upserts on (user_id, strava_activity_id) and session
        creation skips any activity already linked, so re-running the same range
        is safe and is the intended way to repair a partial backfill.
        """
        connection = StravaRepository.get_connection_row(user_id)
        if not connection:
            raise StravaNotConnectedError()

        if after is None:
            after = datetime.now(UTC) - timedelta(days=days or 30)
        if before is None:
            before = datetime.now(UTC)
        if after >= before:
            raise ValidationError("`after` must be earlier than `before`")

        if auto_create is None:
            auto_create = bool(connection.get("auto_create_sessions"))

        access_token = cls.get_access_token(user_id)
        summaries = cls._fetch_all_pages(access_token, after, before)

        tally = {
            "created": 0,
            "updated": 0,
            "skipped": 0,
            "detail_calls": 0,
            "sessions_created": 0,
        }
        detail_budget_hit = False

        for summary in summaries:
            activity_id = str(summary.get("id") or "")
            if not activity_id or activity_id == "None":
                tally["skipped"] += 1
                continue

            budget_left = _ACTIVITY_DETAIL_BUDGET - tally["detail_calls"]
            detail, spent = cls._maybe_fetch_detail(
                user_id, access_token, activity_id, budget_left
            )
            tally["detail_calls"] += spent
            if spent == 0 and budget_left <= 0:
                detail_budget_hit = True

            cls._store_activity(
                user_id, activity_id, summary, detail, auto_create, tally
            )

        StravaRepository.set_last_synced(user_id)

        result = {
            "fetched": len(summaries),
            **tally,
            "range_start": after.isoformat(),
            "range_end": before.isoformat(),
        }
        if detail_budget_hit:
            # Surfaced rather than silently truncated — the caller can re-run a
            # narrower range to pick up the heart rate this pass skipped.
            result["detail_budget_exhausted"] = True
            result["warning"] = (
                f"Heart-rate detail was fetched for the first {_ACTIVITY_DETAIL_BUDGET} "
                "activities only. Re-run over a narrower date range to fill in the rest."
            )
        logger.info("Strava sync — user_id=%s %s", user_id, result)
        return result

    @classmethod
    def _auto_create_session(cls, user_id: int, cached: dict) -> bool:
        """Create a needs_review session for a cached activity. True if created."""
        if not is_importable(cached):
            return False
        return cls.import_activity(user_id, cached) is not None

    @classmethod
    def import_activity(cls, user_id: int, cached: dict) -> int | None:
        """Create a session from a cached activity and link it back. Returns id.

        The session is written with ``source='strava'`` and ``needs_review=True``
        so it shows up for confirmation rather than passing itself off as
        hand-logged data.
        """
        if cached.get("session_id") is not None:
            return None

        start_local = cached.get("start_time_local") or cached.get("start_time")
        if isinstance(start_local, str):
            start_local = _parse_dt(start_local)
        if start_local is None:
            logger.warning(
                "Strava activity %s has no usable start time — skipped",
                cached.get("strava_activity_id"),
            )
            return None

        session_date: date = start_local.date()
        seconds = cached.get("elapsed_time_sec") or cached.get("moving_time_sec") or 0
        duration_mins = max(1, int(round(seconds / 60.0)))

        class_type = classify_activity(cached, cls._default_bjj_class_type(user_id))

        session_id = SessionRepository.create(
            user_id=user_id,
            session_date=session_date,
            class_type=class_type,
            gym_name=cls._default_gym_name(user_id),
            class_time=start_local.strftime("%H:%M"),
            duration_mins=duration_mins,
            intensity=derive_intensity(cached),
            notes=f"Imported from Strava: {cached.get('name') or 'Untitled'}",
            source="strava",
            needs_review=True,
        )

        SessionRepository.update(
            user_id=user_id,
            session_id=session_id,
            strava_activity_id=str(cached.get("strava_activity_id")),
            strava_activity_name=cached.get("name"),
            strava_activity_type=cached.get("sport_type")
            or cached.get("activity_type"),
            strava_avg_hr=cached.get("avg_heart_rate"),
            strava_max_hr=cached.get("max_heart_rate"),
            strava_calories=cached.get("calories"),
            strava_duration_min=round(seconds / 60.0, 1) if seconds else None,
            strava_suffer_score=cached.get("suffer_score"),
            strava_distance_m=cached.get("distance_m"),
            # SessionService.update_session clears needs_review on any edit as a
            # "user has seen this" signal. This is a machine write, not a user
            # edit, so re-assert it via the repository.
            needs_review=True,
        )

        StravaRepository.link_session(user_id, cached["id"], session_id)
        return session_id

    @classmethod
    def list_importable(cls, user_id: int, limit: int = 100) -> list[dict]:
        """Unlinked activities with the class type they would import as."""
        default_bjj = cls._default_bjj_class_type(user_id)
        out = []
        for activity in StravaRepository.list_unlinked(user_id, limit):
            out.append(
                {
                    **activity,
                    "suggested_class_type": classify_activity(activity, default_bjj),
                    "suggested_intensity": derive_intensity(activity),
                    "importable": is_importable(activity),
                }
            )
        return out
