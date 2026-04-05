#!/usr/bin/env python
"""Manually apply pending migrations.

Run from repo root: `python apply_migrations.py`

NOTE on import path: the repo has a `rivaflow/` directory at the root that
contains the actual Python package (`rivaflow/rivaflow/`). Because the outer
`rivaflow/` lacks an `__init__.py`, Python treats it as a namespace package
and can shadow the editable install (`pip install -e rivaflow/`). To make
this script work reliably from the repo root, we explicitly add the outer
`rivaflow/` to sys.path so the inner package directory is discoverable as
a regular package.
"""

import os
import sys

# Ensure the inner `rivaflow` package (at <repo>/rivaflow/rivaflow/) is on
# the import path even when CWD is the repo root.
_HERE = os.path.dirname(os.path.abspath(__file__))
_PACKAGE_PARENT = os.path.join(_HERE, "rivaflow")
if os.path.isdir(os.path.join(_PACKAGE_PARENT, "rivaflow")):
    sys.path.insert(0, _PACKAGE_PARENT)

from rivaflow.db.database import init_db  # noqa: E402

if __name__ == "__main__":
    print("Applying pending migrations...")
    init_db()
    print("Done!")
