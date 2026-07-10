"""Wave 3.6 — ingest device_tz persistence helper (pure logic; DB calls mocked).

`_persist_device_tz` is the factored-out piece of the /whoop/ingest route that
validates a phone-reported IANA tz and writes it to profile.device_tz only when
it's a genuine change — never per-batch, never on an invalid tz, never raising
(the ingest route must always return 200 regardless of this helper's outcome).
"""

from __future__ import annotations

from rivaflow.api.routes import whoop as whoop_route
from rivaflow.db.repositories.base_repository import BaseRepository


def test_persist_skips_when_no_device_tz(monkeypatch):
    calls = {"fetch": 0, "execute": 0}
    monkeypatch.setattr(
        BaseRepository,
        "_fetchone",
        staticmethod(lambda *a, **k: calls.__setitem__("fetch", calls["fetch"] + 1)),
    )
    monkeypatch.setattr(
        BaseRepository,
        "_execute",
        staticmethod(
            lambda *a, **k: calls.__setitem__("execute", calls["execute"] + 1)
        ),
    )
    whoop_route._persist_device_tz(1, None)
    assert calls == {"fetch": 0, "execute": 0}


def test_persist_ignores_invalid_tz(monkeypatch):
    execute_calls = []
    monkeypatch.setattr(
        BaseRepository,
        "_execute",
        staticmethod(lambda *a, **k: execute_calls.append((a, k))),
    )
    # No _fetchone patch needed — an invalid tz must short-circuit before any DB read.
    monkeypatch.setattr(
        BaseRepository,
        "_fetchone",
        staticmethod(
            lambda *a, **k: (_ for _ in ()).throw(AssertionError("should not query"))
        ),
    )
    whoop_route._persist_device_tz(1, "Not/A/Real/Zone")
    assert execute_calls == []


def test_persist_writes_on_genuine_change(monkeypatch):
    monkeypatch.setattr(
        BaseRepository,
        "_fetchone",
        staticmethod(lambda *a, **k: {"device_tz": "Australia/Melbourne"}),
    )
    execute_calls = []
    monkeypatch.setattr(
        BaseRepository,
        "_execute",
        staticmethod(lambda *a, **k: execute_calls.append((a, k))),
    )
    whoop_route._persist_device_tz(1, "America/Chicago")
    assert len(execute_calls) == 1
    query, params = execute_calls[0][0]
    assert "UPDATE profile SET device_tz" in query
    assert params == ("America/Chicago", 1)


def test_persist_skips_when_value_unchanged(monkeypatch):
    monkeypatch.setattr(
        BaseRepository,
        "_fetchone",
        staticmethod(lambda *a, **k: {"device_tz": "America/Chicago"}),
    )
    execute_calls = []
    monkeypatch.setattr(
        BaseRepository,
        "_execute",
        staticmethod(lambda *a, **k: execute_calls.append((a, k))),
    )
    whoop_route._persist_device_tz(1, "America/Chicago")
    assert execute_calls == []


def test_persist_skips_when_no_profile_row_yet(monkeypatch):
    monkeypatch.setattr(BaseRepository, "_fetchone", staticmethod(lambda *a, **k: None))
    execute_calls = []
    monkeypatch.setattr(
        BaseRepository,
        "_execute",
        staticmethod(lambda *a, **k: execute_calls.append((a, k))),
    )
    whoop_route._persist_device_tz(1, "America/Chicago")
    assert execute_calls == []  # no profile row to update — never fabricate one here
