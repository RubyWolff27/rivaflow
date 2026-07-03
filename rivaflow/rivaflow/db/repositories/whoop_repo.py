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

from rivaflow.db.database import convert_query, get_connection
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
                (user_id, f["ts"], sha, f.get("session_id"), f["char_uuid"],
                 f.get("packet_type"), f.get("seq"), hex_)
            )
        received = WhoopRepository._insert_ignore(
            "INSERT INTO whoop_raw_frames "
            "(user_id, ts, frame_sha256, session_id, char_uuid, packet_type, seq, frame_hex) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (user_id, ts, frame_sha256) DO NOTHING",
            rows,
        )
        if rejected:
            logger.warning("whoop raw ingest — user_id=%s rejected=%s non-hex frames", user_id, rejected)
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
            (user_id, s["ts"], s.get("rmssd"), s.get("rr_count"), s.get("window_s"), s.get("at_rest"))
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
    def log_ingest(user_id: int, device: str | None, kind: str | None, counts: dict,
                   span_start: str | None, span_end: str | None) -> None:
        query = convert_query(
            "INSERT INTO whoop_ingest_log "
            "(user_id, device, kind, raw_frames, hr, rr, hrv, battery, deduped, span_start, span_end) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        )
        with get_connection() as conn:
            conn.cursor().execute(query, (
                user_id, device, kind, counts.get("raw", 0), counts.get("hr", 0),
                counts.get("rr", 0), counts.get("hrv", 0), counts.get("battery", 0),
                counts.get("rejected", 0), span_start, span_end,
            ))

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
    def hrv_range(user_id: int, days: int = 30, at_rest_only: bool = True) -> list[dict]:
        """HRV (RMSSD) samples over the last `days`, ascending — drives the readiness baseline.
        Wrist-PPG HRV is only trustworthy at rest, so at_rest_only filters the noise by default."""
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
            convert_query("SELECT ts, bpm FROM whoop_hr WHERE user_id = ? AND ts >= ? ORDER BY ts ASC"),
            (user_id, cutoff),
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
