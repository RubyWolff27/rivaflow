"""Shared root-logger configuration — JSON in production, plain text elsewhere.

Used by both the API process (rivaflow.api.main) and the scheduler sidecar
(rivaflow.scheduler_main) so their log lines share one format regardless of
which process emits them.
"""

import logging

from rivaflow.core.settings import settings


def configure_logging() -> None:
    """Configure the root logger. Idempotent — safe to call more than once."""
    if settings.IS_PRODUCTION:
        try:
            from pythonjsonlogger.json import JsonFormatter

            handler = logging.StreamHandler()
            handler.setFormatter(
                JsonFormatter(
                    fmt="%(asctime)s %(name)s %(levelname)s %(message)s",
                    datefmt="%Y-%m-%dT%H:%M:%S",
                )
            )
            logging.root.handlers = [handler]
            logging.root.setLevel(logging.INFO)
            return
        except ImportError:
            pass

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
