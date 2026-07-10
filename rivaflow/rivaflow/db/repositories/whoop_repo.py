"""Repository for the subscription-free WHOOP data platform (Phase 1a ingest).

Populated by the Goose iOS app's WhoopVpsUploader. Raw-first + idempotent:
whoop_raw_frames is the immutable source of truth; decoded streams are rebuildable
from it. Every write is user-scoped and dedup-safe (ON CONFLICT DO NOTHING), so the
app can retry a batch after a flaky connection without creating duplicates.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from rivaflow.db.database import convert_query, execute_insert, get_connection
from rivaflow.db.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


def _is_hex(s: str) -> bool:
    """True only for a valid, even-length hex string (guards the raw-frame ingest)."""
    if not s or len(s) % 2 != 0:
        return False
    try:
        bytes.fromhex(s)
        return True
    except ValueError:
        return False


# Suggested first-class tags surfaced in the tag-vocabulary endpoint — mirrors the
# examples add_tag_endpoint's docstring lists (routes/whoop.py) so the "Tag Today"
# picker always offers them even before the user has ever applied one.
BUILTIN_TAGS: tuple[str, ...] = (
    "alcohol",
    "late-training",
    "ill",
    "poor-sleep",
    "travel",
    "sabbath-rest",
)


class WhoopRepository:
    """Idempotent, user-scoped ingest for the whoop_* stream tables."""

    @staticmethod
    def _insert_ignore(query: str, rows: list[tuple]) -> int:
        """executemany an INSERT ... ON CONFLICT DO NOTHING; returns rows *received*.
        (Exact dedup counts are driver-dependent under executemany; ON CONFLICT
        guarantees idempotency regardless.)"""
        if not rows:
            return 0
        with get_connection() as conn:
            conn.cursor().executemany(convert_query(query), rows)
        return len(rows)

    @staticmethod
    def ingest_raw_frames(user_id: int, frames: list[dict]) -> dict:
        rows: list[tuple] = []
        rejected = 0
        for f in frames:
            hex_ = (f.get("hex") or "").strip().lower()
            if not _is_hex(hex_):
                rejected += 1
                continue
            sha = hashlib.sha256(hex_.encode("ascii")).hexdigest()
            rows.append(
                (
                    user_id,
                    f["ts"],
                    sha,
                    f.get("session_id"),
                    f["char_uuid"],
                    f.get("packet_type"),
                    f.get("seq"),
                    hex_,
                )
            )
        received = WhoopRepository._insert_ignore(
            "INSERT INTO whoop_raw_frames "
            "(user_id, ts, frame_sha256, session_id, char_uuid, packet_type, seq, frame_hex) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (user_id, ts, frame_sha256) DO NOTHING",
            rows,
        )
        if rejected:
            logger.warning(
                "whoop raw ingest — user_id=%s rejected=%s non-hex frames",
                user_id,
                rejected,
            )
        return {"received": received, "rejected": rejected}

    @staticmethod
    def ingest_hr(user_id: int, samples: list[dict]) -> int:
        rows = [(user_id, s["ts"], s["bpm"], s.get("session_id")) for s in samples]
        return WhoopRepository._insert_ignore(
            "INSERT INTO whoop_hr (user_id, ts, bpm, session_id) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (user_id, ts) DO NOTHING",
            rows,
        )

    @staticmethod
    def ingest_rr(user_id: int, samples: list[dict]) -> int:
        rows = [(user_id, s["ts"], s["rr_ms"], s.get("session_id")) for s in samples]
        return WhoopRepository._insert_ignore(
            "INSERT INTO whoop_rr (user_id, ts, rr_ms, session_id) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (user_id, ts, rr_ms) DO NOTHING",
            rows,
        )

    @staticmethod
    def ingest_hrv(user_id: int, samples: list[dict]) -> int:
        rows = [
            (
                user_id,
                s["ts"],
                s.get("rmssd"),
                s.get("rr_count"),
                s.get("window_s"),
                s.get("at_rest"),
            )
            for s in samples
        ]
        return WhoopRepository._insert_ignore(
            "INSERT INTO whoop_hrv (user_id, ts, rmssd, rr_count, window_s, at_rest) "
            "VALUES (?, ?, ?, ?, ?, ?) ON CONFLICT (user_id, ts) DO NOTHING",
            rows,
        )

    @staticmethod
    def ingest_battery(user_id: int, samples: list[dict]) -> int:
        rows = [(user_id, s["ts"], s.get("soc"), s.get("charging")) for s in samples]
        return WhoopRepository._insert_ignore(
            "INSERT INTO whoop_battery (user_id, ts, soc, charging) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (user_id, ts) DO NOTHING",
            rows,
        )

    @staticmethod
    def log_ingest(
        user_id: int,
        device: str | None,
        kind: str | None,
        counts: dict,
        span_start: str | None,
        span_end: str | None,
    ) -> None:
        query = convert_query(
            "INSERT INTO whoop_ingest_log "
            "(user_id, device, kind, raw_frames, hr, rr, hrv, battery, deduped, span_start, span_end) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        with get_connection() as conn:
            conn.cursor().execute(
                query,
                (
                    user_id,
                    device,
                    kind,
                    counts.get("raw", 0),
                    counts.get("hr", 0),
                    counts.get("rr", 0),
                    counts.get("hrv", 0),
                    counts.get("battery", 0),
                    counts.get("rejected", 0),
                    span_start,
                    span_end,
                ),
            )

    # ── Read side (shared: RivaFlow UI, health dashboard, LLM/MCP all consume these) ──

    @staticmethod
    def hr_range(user_id: int, start_iso: str, end_iso: str) -> list[dict]:
        """HR samples within [start, end], ascending — for session zones + charts."""
        return BaseRepository._fetchall(
            convert_query(
                "SELECT ts, bpm FROM whoop_hr WHERE user_id = ? AND ts >= ? AND ts <= ? ORDER BY ts ASC"
            ),
            (user_id, start_iso, end_iso),
        )

    @staticmethod
    def hrv_range(
        user_id: int, days: int = 30, at_rest_only: bool = True
    ) -> list[dict]:
        """HRV (RMSSD) samples over the last `days`, ascending — drives the readiness baseline.
        Wrist-PPG HRV is only trustworthy at rest, so at_rest_only filters the noise by default.
        """
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        rest = "AND at_rest = ? " if at_rest_only else ""
        params = (user_id, True, cutoff) if at_rest_only else (user_id, cutoff)
        return BaseRepository._fetchall(
            convert_query(
                "SELECT ts, rmssd FROM whoop_hrv WHERE user_id = ? AND rmssd IS NOT NULL "
                f"{rest}AND ts >= ? ORDER BY ts ASC"
            ),
            params,
        )

    @staticmethod
    def recent_hr(user_id: int, hours: int = 6) -> list[dict]:
        """Recent HR series (last `hours`) — for the live/health dashboard."""
        cutoff = (datetime.now(UTC) - timedelta(hours=hours)).isoformat()
        return BaseRepository._fetchall(
            convert_query(
                "SELECT ts, bpm FROM whoop_hr WHERE user_id = ? AND ts >= ? ORDER BY ts ASC"
            ),
            (user_id, cutoff),
        )

    @staticmethod
    def rr_range(user_id: int, days: int = 14) -> list[dict]:
        """RR intervals over the last `days`, time-ordered — the raw truth for deriving HRV (RMSSD)."""
        cutoff = (datetime.now(UTC) - timedelta(days=days)).isoformat()
        return BaseRepository._fetchall(
            convert_query(
                "SELECT ts, rr_ms FROM whoop_rr WHERE user_id = ? AND ts >= ? ORDER BY ts ASC"
            ),
            (user_id, cutoff),
        )

    @staticmethod
    def rr_range_between(user_id: int, start_iso: str, end_iso: str) -> list[dict]:
        """RR intervals within [start, end] (inclusive), ascending — the bounded-window counterpart to
        hr_range, for computing one specific historical day's rollup (whoop_daily_agg, Wave 3.4) where
        rr_range's 'last N days from now' doesn't line up with an arbitrary past local day.
        """
        return BaseRepository._fetchall(
            convert_query(
                "SELECT ts, rr_ms FROM whoop_rr WHERE user_id = ? AND ts >= ? AND ts <= ? ORDER BY ts ASC"
            ),
            (user_id, start_iso, end_iso),
        )

    @staticmethod
    def hr_count_range(user_id: int, start_iso: str, end_iso: str) -> int:
        """COUNT(*) of whoop_hr rows in [start, end] — an index range-scan count, no row materialization.
        Half of the whoop_daily_agg staleness check (see rr_count_range): a stored rollup whose CURRENT raw
        count no longer matches the count it was computed from has had rows land late (the phone's offline
        spool / a historical drain) and must be recomputed."""
        row = BaseRepository._fetchone(
            convert_query(
                "SELECT COUNT(*) AS n FROM whoop_hr WHERE user_id = ? AND ts >= ? AND ts <= ?"
            ),
            (user_id, start_iso, end_iso),
        )
        return int(row["n"]) if row else 0

    @staticmethod
    def rr_count_range(user_id: int, start_iso: str, end_iso: str) -> int:
        """COUNT(*) of whoop_rr rows in [start, end] — see hr_count_range."""
        row = BaseRepository._fetchone(
            convert_query(
                "SELECT COUNT(*) AS n FROM whoop_rr WHERE user_id = ? AND ts >= ? AND ts <= ?"
            ),
            (user_id, start_iso, end_iso),
        )
        return int(row["n"]) if row else 0

    # ── Daily aggregate rollups (whoop_daily_agg — Wave 3.4, append-only per-day compute cache) ──

    @staticmethod
    def get_daily_agg(user_id: int, day: str) -> dict | None:
        """The stored rollup for one user/day, or None if this day has never been computed."""
        return BaseRepository._fetchone(
            convert_query(
                "SELECT metrics_json, deriver_version, sample_count, complete, updated_at "
                "FROM whoop_daily_agg WHERE user_id = ? AND day = ?"
            ),
            (user_id, day),
        )

    @staticmethod
    def upsert_daily_agg(
        user_id: int,
        day: str,
        metrics_json: str,
        deriver_version: str,
        sample_count: int,
        complete: bool,
    ) -> None:
        """Insert or replace one day's rollup. A day is only ever REPLACED by a fresher computation of the
        SAME day (deriver-version bump, or late-arriving raw data changing its sample_count) — never
        deleted, so the table stays append-only in spirit."""
        BaseRepository._execute(
            convert_query(
                "INSERT INTO whoop_daily_agg "
                "(user_id, day, metrics_json, deriver_version, sample_count, complete, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP) "
                "ON CONFLICT (user_id, day) DO UPDATE SET "
                "metrics_json = EXCLUDED.metrics_json, deriver_version = EXCLUDED.deriver_version, "
                "sample_count = EXCLUDED.sample_count, complete = EXCLUDED.complete, "
                "updated_at = CURRENT_TIMESTAMP"
            ),
            (user_id, day, metrics_json, deriver_version, sample_count, complete),
        )

    @staticmethod
    def latest_capture(user_id: int) -> dict | None:
        """Most recent ingest heartbeat (capture-health)."""
        return BaseRepository._fetchone(
            convert_query(
                "SELECT ingested_at, device, kind, raw_frames, hr, rr, span_start, span_end "
                "FROM whoop_ingest_log WHERE user_id = ? ORDER BY ingested_at DESC LIMIT 1"
            ),
            (user_id,),
        )

    # ── Journal tags (P1 — Capture & Labels) ─────────────────────────────
    # A tag marks that something happened on a local day (alcohol, late-training, ill, poor-sleep,
    # travel, sabbath-rest). Feeds B11 behaviour correlation + the B6 validation gate ("ill" = onset).

    @staticmethod
    def add_tag(user_id: int, day: str, tag: str) -> int:
        """Idempotent add of one (day, tag) for a user."""
        return WhoopRepository._insert_ignore(
            "INSERT INTO whoop_tags (user_id, day, tag) VALUES (?, ?, ?) "
            "ON CONFLICT (user_id, day, tag) DO NOTHING",
            [(user_id, day, tag)],
        )

    @staticmethod
    def list_tags(
        user_id: int, start: str | None = None, end: str | None = None
    ) -> list[dict]:
        """Tags for a user, optionally bounded to [start, end] local days (newest first)."""
        query = "SELECT day, tag, created_at FROM whoop_tags WHERE user_id = ?"
        params: list = [user_id]
        if start:
            query += " AND day >= ?"
            params.append(start)
        if end:
            query += " AND day <= ?"
            params.append(end)
        query += " ORDER BY day DESC, tag"
        return BaseRepository._fetchall(convert_query(query), tuple(params))

    @staticmethod
    def remove_tag(user_id: int, day: str, tag: str) -> None:
        """Delete one (day, tag) for a user."""
        BaseRepository._execute(
            convert_query(
                "DELETE FROM whoop_tags WHERE user_id = ? AND day = ? AND tag = ?"
            ),
            (user_id, day, tag),
        )

    @staticmethod
    def tagged_days(user_id: int, tag: str) -> set[str]:
        """The set of 'YYYY-MM-DD' local days carrying `tag` — the shape analytics consume."""
        rows = BaseRepository._fetchall(
            convert_query("SELECT day FROM whoop_tags WHERE user_id = ? AND tag = ?"),
            (user_id, tag),
        )
        return {str(r["day"])[:10] for r in rows}

    @staticmethod
    def distinct_tags(user_id: int) -> list[str]:
        """The sorted, deduped set of tag strings this user has ever applied — feeds the
        tag-vocabulary endpoint (B4) alongside the built-in suggestions."""
        rows = BaseRepository._fetchall(
            convert_query(
                "SELECT DISTINCT tag FROM whoop_tags WHERE user_id = ? ORDER BY tag"
            ),
            (user_id,),
        )
        return [str(r["tag"]) for r in rows]

    @staticmethod
    def tag_vocabulary(user_id: int) -> list[str]:
        """BUILTIN_TAGS (in their canonical order) + any distinct tag this user has
        actually applied that isn't already a built-in — so a one-off custom tag is
        offered again next time, and the picker never starts empty."""
        used = WhoopRepository.distinct_tags(user_id)
        extras = [t for t in used if t not in BUILTIN_TAGS]
        return list(BUILTIN_TAGS) + extras

    # ── Timestamped workout sessions (real start/end window so HR can attach) ──

    @staticmethod
    def create_whoop_session(
        user_id: int,
        activity: str,
        started_at: str,
        ended_at: str | None = None,
        source: str = "app",
    ) -> int:
        """Log a timestamped workout session and return its id. `started_at`/`ended_at` are ISO8601."""
        with get_connection() as conn:
            cursor = conn.cursor()
            return execute_insert(
                cursor,
                "INSERT INTO whoop_sessions (user_id, activity, started_at, ended_at, source) "
                "VALUES (?, ?, ?, ?, ?)",
                (user_id, activity, started_at, ended_at, source),
            )

    @staticmethod
    def end_whoop_session(session_id: int, ended_at: str, user_id: int) -> bool:
        """Close an open session by stamping its `ended_at` (ISO8601).

        Scoped to the owning `user_id` so a key holder cannot close another
        user's session by guessing its id (cross-user IDOR). Returns True iff a
        row was updated, letting the route 404 on a missing/foreign session.
        """
        cursor = BaseRepository._execute(
            convert_query(
                "UPDATE whoop_sessions SET ended_at = ? WHERE id = ? AND user_id = ?"
            ),
            (ended_at, session_id, user_id),
        )
        return bool(cursor.rowcount and cursor.rowcount > 0)

    @staticmethod
    def list_whoop_sessions(user_id: int, limit: int = 10) -> list[dict]:
        """A user's logged workout sessions, most recent first."""
        return BaseRepository._fetchall(
            convert_query(
                "SELECT id, activity, started_at, ended_at, source, created_at "
                "FROM whoop_sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT ?"
            ),
            (user_id, limit),
        )

    # ── Prevention alerts (P2 — delivery log + cooldown state) ───────────

    @staticmethod
    def record_alert(
        user_id: int, day: str, alert_key: str, tier: str, headline: str | None
    ) -> int:
        """Idempotently record that a safety alert fired for a (day, key). Doubles as the cooldown state."""
        return WhoopRepository._insert_ignore(
            "INSERT INTO whoop_alerts (user_id, day, alert_key, tier, headline) "
            "VALUES (?, ?, ?, ?, ?) ON CONFLICT (user_id, day, alert_key) DO NOTHING",
            [(user_id, day, alert_key, tier, headline)],
        )

    @staticmethod
    def last_alert_days(user_id: int) -> dict[str, str]:
        """Most-recent fire day per alert_key — the cooldown map the digest consumes ({key: 'YYYY-MM-DD'})."""
        rows = BaseRepository._fetchall(
            convert_query(
                "SELECT alert_key, MAX(day) AS last_day FROM whoop_alerts "
                "WHERE user_id = ? GROUP BY alert_key"
            ),
            (user_id,),
        )
        return {
            r["alert_key"]: str(r["last_day"])[:10] for r in rows if r.get("last_day")
        }

    @staticmethod
    def recent_alerts(user_id: int, limit: int = 60) -> list[dict]:
        """Recent fired alerts (newest first) — the prevention-log timeline (P3.4)."""
        return BaseRepository._fetchall(
            convert_query(
                "SELECT day, alert_key, tier, headline, created_at FROM whoop_alerts "
                "WHERE user_id = ? ORDER BY day DESC, created_at DESC LIMIT ?"
            ),
            (user_id, limit),
        )

    # ── Cockpit snapshot (pre-computed page — scheduled render, instant serve) ──

    @staticmethod
    def get_cockpit_snapshot(user_id: int) -> dict | None:
        """The stored pre-computed cockpit page for a user ({html, rendered_at}) or None if never built."""
        return BaseRepository._fetchone(
            convert_query(
                "SELECT html, rendered_at FROM whoop_cockpit_snapshot WHERE user_id = ?"
            ),
            (user_id,),
        )

    @staticmethod
    def get_cockpit_metrics(user_id: int) -> dict | None:
        """The structured metrics JSON contract behind the snapshot, or None.

        Returns {metrics_json (str), deriver_version, rendered_at}; consumers
        json.loads the metrics_json. This is the data the cockpit rendered from,
        readable instantly without the ~40s recompute.
        """
        return BaseRepository._fetchone(
            convert_query(
                "SELECT metrics_json, deriver_version, rendered_at "
                "FROM whoop_cockpit_snapshot WHERE user_id = ?"
            ),
            (user_id,),
        )

    @staticmethod
    def upsert_cockpit_snapshot(
        user_id: int,
        html: str,
        metrics_json: str | None = None,
        deriver_version: str | None = None,
    ) -> None:
        """Store (or replace) a user's pre-computed cockpit HTML + structured
        metrics JSON, stamping rendered_at to now."""
        BaseRepository._execute(
            convert_query(
                "INSERT INTO whoop_cockpit_snapshot "
                "(user_id, html, metrics_json, deriver_version) VALUES (?, ?, ?, ?) "
                "ON CONFLICT (user_id) DO UPDATE SET html = EXCLUDED.html, "
                "metrics_json = EXCLUDED.metrics_json, "
                "deriver_version = EXCLUDED.deriver_version, rendered_at = NOW()"
            ),
            (user_id, html, metrics_json, deriver_version),
        )
