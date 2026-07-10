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

import asyncio
import os
import signal
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
#
# Regression context (2026-07): the sidecar crash-looped in prod with
# `RuntimeError: no running event loop` from apscheduler/schedulers/asyncio.py
# — AsyncIOScheduler.start() binds to whatever loop is running when it's
# called, and a bare synchronous _run() has no loop at all. The fix moved
# everything from start_scheduler() onward into asyncio.run(_amain()).
# test_run_hosts_start_scheduler_inside_a_running_event_loop below pins that
# contract directly by having the stubbed start_scheduler() call
# asyncio.get_running_loop() itself — verified to fail against the prior
# synchronous implementation (see PR description / commit message for the
# before/after repro).
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
    # No event loop should even be spun up when the DB never comes up.


def test_run_hosts_start_scheduler_inside_a_running_event_loop(monkeypatch):
    """start_scheduler() must observe a running asyncio loop (AsyncIOScheduler.start()
    binds to it) — this is exactly the contract the sync-_run() bug violated."""
    import rivaflow.scheduler_main as sched_main

    monkeypatch.setattr(sched_main, "_wait_for_db", lambda: True)
    order: list[str] = []

    def _fake_start_scheduler() -> None:
        asyncio.get_running_loop()  # raises RuntimeError outside asyncio.run()
        order.append("start")

    monkeypatch.setattr(sched_main, "start_scheduler", _fake_start_scheduler)
    monkeypatch.setattr(sched_main, "stop_scheduler", lambda: order.append("stop"))

    def _fast_stop(loop: asyncio.AbstractEventLoop, stop_event: asyncio.Event) -> None:
        # Simulate a shutdown signal arriving shortly after startup, without
        # touching the real process signal handlers from inside a test run.
        loop.call_later(0.01, stop_event.set)

    monkeypatch.setattr(sched_main, "_install_signal_handlers", _fast_stop)

    exit_code = sched_main._run()

    assert order == ["start", "stop"]
    assert exit_code == 0


def test_amain_starts_then_stops_scheduler_in_order(monkeypatch):
    """Drive _amain directly with a pre-built stop_event set shortly after start."""
    import rivaflow.scheduler_main as sched_main

    order: list[str] = []
    monkeypatch.setattr(sched_main, "start_scheduler", lambda: order.append("start"))
    monkeypatch.setattr(sched_main, "stop_scheduler", lambda: order.append("stop"))
    monkeypatch.setattr(
        sched_main, "_install_signal_handlers", lambda _loop, _event: None
    )

    async def _drive() -> int:
        event = asyncio.Event()
        asyncio.get_running_loop().call_later(0.01, event.set)
        return await sched_main._amain(stop_event=event)

    exit_code = asyncio.run(_drive())

    assert order == ["start", "stop"]
    assert exit_code == 0


def test_install_signal_handlers_sets_event_on_real_sigterm():
    """SIGTERM (or SIGINT) delivered to the sidecar must flip the asyncio stop event."""
    import rivaflow.scheduler_main as sched_main

    original_sigterm = signal.getsignal(signal.SIGTERM)
    original_sigint = signal.getsignal(signal.SIGINT)

    async def _probe() -> None:
        loop = asyncio.get_running_loop()
        event = asyncio.Event()
        sched_main._install_signal_handlers(loop, event)
        try:
            assert not event.is_set()
            os.kill(os.getpid(), signal.SIGTERM)
            await asyncio.wait_for(event.wait(), timeout=2)
            assert event.is_set()
        finally:
            loop.remove_signal_handler(signal.SIGTERM)
            loop.remove_signal_handler(signal.SIGINT)

    try:
        asyncio.run(_probe())
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
