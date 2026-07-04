#!/usr/bin/env python
"""Apply all pending database migrations.

Run from repo root: `python apply_migrations.py`

Uses the real migration runner (`rivaflow.db.migrate.run_migrations`), which
applies every pending `*_pg.sql` migration in order and records them in
`schema_migrations`. Previously this script only called `init_db()`, which
creates the migrations tracking table but does NOT apply migration SQL — so in
CI the schema was only ever built lazily by the test fixtures, and any migration
that failed there left tables missing with no visible log.

NOTE on import path: the repo has a `rivaflow/` directory at the root that
contains the actual Python package (`rivaflow/rivaflow/`). Because the outer
`rivaflow/` lacks an `__init__.py`, Python treats it as a namespace package
and can shadow the editable install (`pip install -e rivaflow/`). To make
this script work reliably from the repo root, we explicitly add the outer
`rivaflow/` to sys.path so the inner package directory is discoverable as
a regular package.
"""

import logging
import os
import sys

# Ensure the inner `rivaflow` package (at <repo>/rivaflow/rivaflow/) is on
# the import path even when CWD is the repo root.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_PARENT = os.path.join(_HERE, "rivaflow")
if os.path.isdir(os.path.join(_PACKAGE_PARENT, "rivaflow")):
    sys.path.insert(0, _PACKAGE_PARENT)

from rivaflow.db.database import init_db  # noqa: E402
from rivaflow.db.migrate import run_migrations  # noqa: E402

if __name__ == "__main__":
    # Surface per-migration progress so a failed/skipped migration is visible in CI logs.
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    print("Initialising migrations tracking table...")
    init_db()
    print("Applying all pending migrations...")
    run_migrations()
    print("Done!")
