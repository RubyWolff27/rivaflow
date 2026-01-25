#!/usr/bin/env python
"""Manually apply pending migrations."""
from rivaflow.db.database import init_db

if __name__ == "__main__":
    print("Applying pending migrations...")
    init_db()
    print("Done!")
