"""Standalone scheduler sidecar entrypoint: ``python -m rivaflow.scheduler_main``.

APScheduler used to start inside every gunicorn UvicornWorker. The cockpit
snapshot build (~128s) exceeds gunicorn's ``--timeout 120``, so gunicorn
SIGABRTs the worker mid-build — the scheduled snapshot silently fails, any
live request on that worker dies with it, and because one scheduler runs
per worker every job double-fires (only a PG advisory lock guards
collisions). This process owns scheduling exclusively in prod instead: the
API's own ``start_scheduler()`` call is gated off via
``RIVAFLOW_RUN_SCHEDULER=0`` (see ``rivaflow.api.main``), and
docker-compose.prod.yml runs this module as its own `scheduler` service.

``core/scheduler.py`` uses APScheduler's AsyncIOScheduler, which binds to
whatever asyncio loop is running when ``.start()`` is called — it ran fine
inside the old in-process setup because uvicorn's own loop was already
running. A bare synchronous ``_run()`` has no loop at all, so
``start_scheduler()`` raised ``RuntimeError: no running event loop`` and the
sidecar crash-looped. The DB wait stays synchronous (it has nothing to do
with asyncio); everything from ``start_scheduler()`` onward runs inside
``asyncio.run(_amain())``.

Does NOT run database migrations (start.sh / the api container already
does) and does NOT import or serve the FastAPI app — this process only
imports what start_scheduler()/stop_scheduler() need.
"""

import asyncio
import logging
import os
import signal
import sys
import time
from collections.abc import Callable
from types import FrameType

from rivaflow.core.logging_config import configure_logging
from rivaflow.core.scheduler import start_scheduler, stop_scheduler
from rivaflow.db.database import get_connection

configure_logging()
logger = logging.getLogger(__name__)

_DB_WAIT_TIMEOUT_SECONDS = 60.0
_DB_WAIT_INITIAL_BACKOFF = 1.0
_DB_WAIT_MAX_BACKOFF = 10.0


def _wait_for_db(
    timeout_seconds: float = _DB_WAIT_TIMEOUT_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> bool:
    """Poll the database with a trivial query until it answers or the timeout elapses.

    Returns True once the DB responds, False if timeout_seconds is exceeded
    without a successful query. Backs off between attempts (1s, 2s, 4s, ...
    capped at _DB_WAIT_MAX_BACKOFF) so a slow-starting Postgres container
    isn't hammered. Runs before the event loop exists — plain blocking I/O.
    """
    deadline = time.monotonic() + timeout_seconds
    backoff = _DB_WAIT_INITIAL_BACKOFF
    attempt = 0
    while True:
        attempt += 1
        try:
            with get_connection() as conn:
                conn.cursor().execute("SELECT 1")
            logger.info("Database reachable after %d attempt(s)", attempt)
            return True
        except Exception as e:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                logger.error(
                    "Database not reachable after %.0fs (%d attempts): %s",
                    timeout_seconds,
                    attempt,
                    e,
                )
                return False
            sleep_for = min(backoff, remaining)
            logger.warning(
                "Database not ready (attempt %d): %s — retrying in %.1fs",
                attempt,
                e,
                sleep_for,
            )
            sleep(sleep_for)
            backoff = min(backoff * 2, _DB_WAIT_MAX_BACKOFF)


def _install_signal_handlers(
    loop: asyncio.AbstractEventLoop, stop_event: asyncio.Event
) -> None:
    """Register SIGTERM/SIGINT to flip stop_event, inside the running loop.

    Prefers loop.add_signal_handler (asyncio-native, Unix only — this is what
    actually runs in prod). Falls back to signal.signal + call_soon_threadsafe
    on platforms where add_signal_handler isn't implemented (e.g. Windows dev
    machines), since a plain signal.signal handler fires on an arbitrary OS
    thread and can't touch the loop's Event directly.
    """

    def _set_stop() -> None:
        logger.info("Received shutdown signal — stopping scheduler")
        stop_event.set()

    try:
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, _set_stop)
    except NotImplementedError:

        def _handle(signum: int, _frame: FrameType | None) -> None:
            logger.info("Received signal %s — stopping scheduler", signum)
            loop.call_soon_threadsafe(stop_event.set)

        signal.signal(signal.SIGTERM, _handle)
        signal.signal(signal.SIGINT, _handle)


async def _amain(stop_event: asyncio.Event | None = None) -> int:
    """Start the scheduler inside a running loop and block until shutdown.

    AsyncIOScheduler.start() must be called with a loop already running
    (it binds to it) — hence this being async and driven via asyncio.run(),
    rather than start_scheduler() being called from plain sync code.
    """
    loop = asyncio.get_running_loop()
    event = stop_event if stop_event is not None else asyncio.Event()
    _install_signal_handlers(loop, event)

    start_scheduler()
    logger.info(
        "Scheduler sidecar running (pid=%d) — waiting for shutdown signal", os.getpid()
    )

    await event.wait()

    stop_scheduler()
    logger.info("Scheduler sidecar exiting cleanly")
    return 0


def _run() -> int:
    """Sync entrypoint: bounded DB wait, then host the scheduler in a real event loop."""
    if not _wait_for_db():
        return 1

    return asyncio.run(_amain())


def main() -> None:
    sys.exit(_run())


if __name__ == "__main__":
    main()
