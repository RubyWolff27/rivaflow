"""Scheduler sidecar tests (pure — no Postgres, no network).

Covers three surfaces:

1. The env gate (RIVAFLOW_RUN_SCHEDULER via settings.RUN_SCHEDULER) that
   decides whether the API process starts its own in-process scheduler.
2. rivaflow.scheduler_main — the standalone `python -m rivaflow.scheduler_main`
   entrypoint that the `scheduler` compose service runs instead.
3. docker-compose.prod.yml — the sidecar service definition and the api
   service's RIVAFLOW_RUN_SCHEDULER override.

See rivaflow/rivaflow/core/scheduler.py for the jobs themselves (unchanged)
and rivaflow/rivaflow/api/main.py for the gate call sites.
"""

from __future__ import annotations

import signal
import threading
from contextlib import contextmanager
from pathlib import Path

import pytest

from rivaflow.core.settings import settings

# ---------------------------------------------------------------------------
# 1. Env gate — rivaflow.api.main._start_scheduler_if_enabled / _stop_scheduler_if_enabled
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _restore_run_scheduler():
    """settings is a process-wide singleton — don't leak RUN_SCHEDULER across tests."""
    original = settings.RUN_SCHEDULER
    yield
    settings.RUN_SCHEDULER = original


def test_gate_unset_or_1_starts_scheduler(monkeypatch):
    """Default (unset/"1") behavior must be byte-identical to pre-sidecar: start_scheduler() runs."""
    import rivaflow.api.main as main_module

    settings.RUN_SCHEDULER = True
    called = []
    monkeypatch.setattr(
        "rivaflow.core.scheduler.start_scheduler", lambda: called.append("start")
    )

    main_module._start_scheduler_if_enabled()

    assert called == ["start"]


def test_gate_0_skips_scheduler_start(monkeypatch, caplog):
    """RIVAFLOW_RUN_SCHEDULER=0 must skip start_scheduler() and log why."""
    import rivaflow.api.main as main_module

    settings.RUN_SCHEDULER = False
    called = []
    monkeypatch.setattr(
        "rivaflow.core.scheduler.start_scheduler", lambda: called.append("start")
    )

    with caplog.at_level("INFO"):
        main_module._start_scheduler_if_enabled()

    assert called == []
    assert any("sidecar" in rec.message for rec in caplog.records)


def test_gate_unset_or_1_stops_scheduler(monkeypatch):
    import rivaflow.api.main as main_module

    settings.RUN_SCHEDULER = True
    called = []
    monkeypatch.setattr(
        "rivaflow.core.scheduler.stop_scheduler", lambda: called.append("stop")
    )

    main_module._stop_scheduler_if_enabled()

    assert called == ["stop"]


def test_gate_0_skips_scheduler_stop(monkeypatch):
    import rivaflow.api.main as main_module

    settings.RUN_SCHEDULER = False
    called = []
    monkeypatch.setattr(
        "rivaflow.core.scheduler.stop_scheduler", lambda: called.append("stop")
    )

    main_module._stop_scheduler_if_enabled()

    assert called == []


# ---------------------------------------------------------------------------
# 2. rivaflow.scheduler_main — DB wait
# ---------------------------------------------------------------------------


class _FakeCursor:
    def execute(self, _query):
        return None


class _FakeConn:
    def cursor(self):
        return _FakeCursor()


@contextmanager
def _fake_get_connection_ok():
    yield _FakeConn()


@contextmanager
def _fake_get_connection_fail():
    raise ConnectionError("db not ready")
    yield  # pragma: no cover — unreachable, required for generator shape


def test_wait_for_db_success_returns_true_without_retrying(monkeypatch):
    import rivaflow.scheduler_main as sched_main

    monkeypatch.setattr(sched_main, "get_connection", _fake_get_connection_ok)
    sleeps: list[float] = []

    result = sched_main._wait_for_db(timeout_seconds=5, sleep=sleeps.append)

    assert result is True
    assert sleeps == []


def test_wait_for_db_failure_retries_then_gives_up(monkeypatch):
    import rivaflow.scheduler_main as sched_main

    monkeypatch.setattr(sched_main, "get_connection", _fake_get_connection_fail)
    sleeps: list[float] = []

    result = sched_main._wait_for_db(timeout_seconds=0.05, sleep=sleeps.append)

    assert result is False
    assert len(sleeps) >= 1  # retried at least once before giving up


# ---------------------------------------------------------------------------
# 2b. rivaflow.scheduler_main — run loop (start → block → stop)
# ---------------------------------------------------------------------------


def test_run_exits_without_starting_scheduler_when_db_unreachable(monkeypatch):
    import rivaflow.scheduler_main as sched_main

    monkeypatch.setattr(sched_main, "_wait_for_db", lambda: False)
    called: list[str] = []
    monkeypatch.setattr(sched_main, "start_scheduler", lambda: called.append("start"))
    monkeypatch.setattr(sched_main, "stop_scheduler", lambda: called.append("stop"))

    exit_code = sched_main._run()

    assert exit_code == 1
    assert called == []


def test_run_starts_then_stops_scheduler_in_order(monkeypatch):
    import rivaflow.scheduler_main as sched_main

    monkeypatch.setattr(sched_main, "_wait_for_db", lambda: True)
    order: list[str] = []
    monkeypatch.setattr(sched_main, "start_scheduler", lambda: order.append("start"))
    monkeypatch.setattr(sched_main, "stop_scheduler", lambda: order.append("stop"))
    # Don't touch the real process signal handlers from inside a test run.
    monkeypatch.setattr(sched_main, "_install_signal_handlers", lambda _event: None)

    stop_event = threading.Event()
    stop_event.set()  # already set — event.wait() returns immediately, no real blocking

    exit_code = sched_main._run(stop_event=stop_event)

    assert order == ["start", "stop"]
    assert exit_code == 0


def test_signal_handler_sets_stop_event():
    """SIGTERM (or SIGINT) delivered to the sidecar must flip the stop event, not exit abruptly."""
    import rivaflow.scheduler_main as sched_main

    event = threading.Event()
    original_sigterm = signal.getsignal(signal.SIGTERM)
    original_sigint = signal.getsignal(signal.SIGINT)
    try:
        sched_main._install_signal_handlers(event)
        handler = signal.getsignal(signal.SIGTERM)

        assert not event.is_set()
        handler(signal.SIGTERM, None)
        assert event.is_set()
    finally:
        signal.signal(signal.SIGTERM, original_sigterm)
        signal.signal(signal.SIGINT, original_sigint)


# ---------------------------------------------------------------------------
# 2c. rivaflow.scheduler_main — no migrations, no API app
# ---------------------------------------------------------------------------


def test_scheduler_main_has_no_migration_or_api_app_import():
    import rivaflow.scheduler_main as sched_main

    source = Path(sched_main.__file__).read_text()
    import_lines = [
        line.strip()
        for line in source.splitlines()
        if line.strip().startswith(("import ", "from "))
    ]

    assert not any("migrate" in line.lower() for line in import_lines)
    assert not any("rivaflow.api" in line for line in import_lines)
    assert not any("fastapi" in line.lower() for line in import_lines)


# ---------------------------------------------------------------------------
# 3. docker-compose.prod.yml — scheduler service + api gate
# ---------------------------------------------------------------------------
#
# PyYAML isn't a declared project dependency (pyproject.toml has no `yaml`/
# `PyYAML` entry), so this asserts on the raw text rather than parsing it,
# to avoid adding a dependency just for one test.


def test_compose_defines_scheduler_sidecar_and_gates_api():
    compose_path = Path(__file__).resolve().parents[3] / "docker-compose.prod.yml"
    assert compose_path.exists(), f"expected docker-compose.prod.yml at {compose_path}"
    text = compose_path.read_text()

    assert (
        "\n  scheduler:\n" in text
    ), "scheduler service missing from docker-compose.prod.yml"
    scheduler_block = text.split("\n  scheduler:\n", 1)[1].split("\n  web:\n", 1)[0]

    assert "command: python -m rivaflow.scheduler_main" in scheduler_block
    assert (
        "condition: service_healthy" in scheduler_block
    )  # mirrors api's db dependency
    assert "restart: unless-stopped" in scheduler_block
    assert "ports:" not in scheduler_block  # no ports — it's not an HTTP service

    api_block = text.split("\n  api:\n", 1)[1].split("\n  scheduler:\n", 1)[0]
    assert 'RIVAFLOW_RUN_SCHEDULER: "0"' in api_block, (
        "api service must disable its in-process scheduler now that the "
        "sidecar owns it — otherwise every job double-fires again"
    )
