"""Timestamped workout sessions — the dedicated whoop_sessions store that lets per-second WHOOP HR attach
to a logged workout (the class `sessions` table only has a date). Covers the repo round-trip, the
session_deepdives HR-attach + no-coverage paths, empty-state, and the write API. Uses the Postgres
test_user/temp_db fixtures.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

_BASE = datetime(2026, 7, 4, 10, 0, 0, tzinfo=timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.isoformat()


class TestWhoopSessionRepo:
    def test_create_list_end_round_trip(self, test_user):
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        uid = test_user["id"]
        sid = WhoopRepository.create_whoop_session(
            uid, "BJJ (gi)", _iso(_BASE), _iso(_BASE + timedelta(hours=1))
        )
        assert isinstance(sid, int) and sid > 0

        rows = WhoopRepository.list_whoop_sessions(uid)
        assert len(rows) == 1
        row = rows[0]
        # Exact dict shape the analytics + backfill/goose payload must match.
        assert set(row.keys()) == {
            "id",
            "activity",
            "started_at",
            "ended_at",
            "source",
            "created_at",
        }
        assert row["id"] == sid
        assert row["activity"] == "BJJ (gi)"
        assert row["source"] == "app"  # default

    def test_open_session_then_end(self, test_user):
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        uid = test_user["id"]
        sid = WhoopRepository.create_whoop_session(uid, "CrossFit", _iso(_BASE))
        assert WhoopRepository.list_whoop_sessions(uid)[0]["ended_at"] is None

        assert (
            WhoopRepository.end_whoop_session(
                sid, _iso(_BASE + timedelta(minutes=45)), uid
            )
            is True
        )
        assert WhoopRepository.list_whoop_sessions(uid)[0]["ended_at"] is not None

    def test_list_is_most_recent_first(self, test_user):
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        uid = test_user["id"]
        WhoopRepository.create_whoop_session(uid, "old", _iso(_BASE))
        WhoopRepository.create_whoop_session(
            uid, "new", _iso(_BASE + timedelta(days=1))
        )
        rows = WhoopRepository.list_whoop_sessions(uid)
        assert [r["activity"] for r in rows] == ["new", "old"]


class TestSessionDeepdives:
    def test_empty_state_returns_list(self, test_user):
        from rivaflow.core.whoop_analytics import session_deepdives

        assert session_deepdives(test_user["id"]) == []

    def test_attaches_hr_to_in_window_session(self, test_user):
        from rivaflow.core.whoop_analytics import session_deepdives
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        uid = test_user["id"]
        WhoopRepository.create_whoop_session(
            uid, "BJJ (gi)", _iso(_BASE), _iso(_BASE + timedelta(hours=1))
        )
        # 90 in-window HR samples, 1s apart — clears the min-sample coverage bar.
        WhoopRepository.ingest_hr(
            uid,
            [{"ts": _iso(_BASE + timedelta(seconds=i)), "bpm": 140} for i in range(90)],
        )

        out = session_deepdives(uid)
        assert len(out) == 1
        item = out[0]
        assert item["label"] == "BJJ (gi)"
        assert item["day"] == "2026-07-04"
        a = item["analytics"]
        assert a["available"] is True
        assert a["avg_hr"] == 140
        assert a["samples"] >= 30
        assert set(a["hr_zone_secs"].keys()) == {1, 2, 3, 4, 5}
        assert a["times"] and a["values"]  # a curve was attached

    def test_no_coverage_session_still_listed(self, test_user):
        from rivaflow.core.whoop_analytics import session_deepdives
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        uid = test_user["id"]
        # A session with no HR anywhere near its window.
        WhoopRepository.create_whoop_session(
            uid, "CrossFit", _iso(_BASE), _iso(_BASE + timedelta(hours=1))
        )
        out = session_deepdives(uid)
        assert len(out) == 1
        assert out[0]["label"] == "CrossFit"
        assert out[0]["analytics"]["available"] is False
        assert out[0]["analytics"]["reason"] == "no HR coverage"

    def test_too_few_samples_marked_no_coverage(self, test_user):
        from rivaflow.core.whoop_analytics import session_deepdives
        from rivaflow.db.repositories.whoop_repo import WhoopRepository

        uid = test_user["id"]
        WhoopRepository.create_whoop_session(
            uid, "Run", _iso(_BASE), _iso(_BASE + timedelta(hours=1))
        )
        # Only 5 in-window samples — below the coverage threshold.
        WhoopRepository.ingest_hr(
            uid,
            [{"ts": _iso(_BASE + timedelta(seconds=i)), "bpm": 130} for i in range(5)],
        )
        out = session_deepdives(uid)
        assert out[0]["analytics"]["available"] is False
        assert out[0]["analytics"]["reason"] == "no HR coverage"


class TestWhoopSessionApi:
    def test_create_and_end_session(self, client, auth_headers):
        r = client.post(
            "/api/v1/whoop/session",
            json={
                "activity": "BJJ (gi)",
                "started_at": _iso(_BASE),
                "ended_at": _iso(_BASE + timedelta(hours=1)),
            },
            headers=auth_headers,
        )
        assert r.status_code == 200, r.text
        sid = r.json()["id"]
        assert isinstance(sid, int)

        r2 = client.patch(
            f"/api/v1/whoop/session/{sid}/end",
            json={"ended_at": _iso(_BASE + timedelta(minutes=50))},
            headers=auth_headers,
        )
        assert r2.status_code == 200, r2.text
        assert r2.json()["ended"]["id"] == sid

    def test_create_requires_auth(self, client):
        r = client.post(
            "/api/v1/whoop/session",
            json={"activity": "BJJ", "started_at": _iso(_BASE)},
        )
        assert r.status_code in (401, 403)
