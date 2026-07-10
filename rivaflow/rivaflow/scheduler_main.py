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

Does NOT run database migrations (start.sh / the api container already
does) and does NOT import or serve the FastAPI app — this process only
imports what start_scheduler()/stop_scheduler() need.
"""

import logging
import os
import signal
import sys
import threading
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
    isn't hammered.
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


def _install_signal_handlers(stop_event: threading.Event) -> None:
    """Register SIGTERM/SIGINT to signal a clean shutdown via stop_event."""

    def _handle(signum: int, _frame: FrameType | None) -> None:
        logger.info("Received signal %s — shutting down scheduler", signum)
        stop_event.set()

    signal.signal(signal.SIGTERM, _handle)
    signal.signal(signal.SIGINT, _handle)


def _run(stop_event: threading.Event | None = None) -> int:
    """Start the scheduler and block until a shutdown signal (or stop_event) fires."""
    if not _wait_for_db():
        return 1

    event = stop_event if stop_event is not None else threading.Event()
    _install_signal_handlers(event)

    start_scheduler()
    logger.info(
        "Scheduler sidecar running (pid=%d) — waiting for shutdown signal", os.getpid()
    )

    event.wait()

    stop_scheduler()
    logger.info("Scheduler sidecar exiting cleanly")
    return 0


def main() -> None:
    sys.exit(_run())


if __name__ == "__main__":
    main()
