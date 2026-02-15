"""Pytest configuration for inner test suite (rivaflow/tests/).

Ensures the installed rivaflow package is used rather than the local
directory of the same name being treated as a namespace package.
"""

import os
import sys

# When running from the repo root (/Users/.../scratch/), Python sees
# the `rivaflow/` directory and treats it as a namespace package,
# shadowing the pip-installed rivaflow package.  Fix by ensuring the
# installed package's parent is at the front of sys.path.
_pkg_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _pkg_dir not in sys.path:
    sys.path.insert(0, _pkg_dir)

# Clear any cached namespace-package import of rivaflow so the real
# package is loaded.
for mod_name in list(sys.modules):
    if mod_name == "rivaflow" or mod_name.startswith("rivaflow."):
        del sys.modules[mod_name]

# Set required environment variables for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-not-production")
os.environ.setdefault("ENV", "test")

import pytest  # noqa: E402

from rivaflow.core.utils.cache import get_cache  # noqa: E402
from rivaflow.db.database import init_db  # noqa: E402


@pytest.fixture(autouse=True)
def _clear_analytics_cache():
    """Clear the in-memory analytics cache before each test."""
    get_cache().clear()
    yield
    get_cache().clear()


@pytest.fixture(autouse=True)
def _disable_rate_limiter():
    """Disable the SlowAPI rate limiter for all tests."""
    from rivaflow.api.rate_limit import limiter

    original = limiter.enabled
    limiter.enabled = False
    yield
    limiter.enabled = original


@pytest.fixture(scope="session", autouse=True)
def _init_test_db():
    """Ensure the test database is initialized once per session."""
    init_db()
