"""Pytest fixtures for RivaFlow tests."""

import os
import shutil
import tempfile
from datetime import date, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Set required environment variables for testing
os.environ.setdefault("SECRET_KEY", "test-secret-key-for-testing-only-not-production")
# Don't set DATABASE_URL - let it use SQLite by default
if "DATABASE_URL" in os.environ:
    del os.environ["DATABASE_URL"]

from rivaflow.core.auth import create_access_token, hash_password
from rivaflow.db.database import init_db
from rivaflow.db.repositories import (
    FriendRepository,
    ProfileRepository,
    ReadinessRepository,
    SessionRepository,
    TechniqueRepository,
    UserRepository,
    VideoRepository,
)


@pytest.fixture(scope="function", autouse=False)
def temp_db(monkeypatch):
    """Create a temporary database for testing."""
    # Create temp directory
    temp_dir = Path(tempfile.mkdtemp())
    temp_db_path = temp_dir / "test.db"

    # Patch config module
    monkeypatch.setattr("rivaflow.config.APP_DIR", temp_dir)
    monkeypatch.setattr("rivaflow.config.DB_PATH", temp_db_path)

    # Also patch database module
    monkeypatch.setattr("rivaflow.db.database.DB_PATH", temp_db_path)
    monkeypatch.setattr("rivaflow.db.database.APP_DIR", temp_dir)

    # Initialize database
    init_db()

    yield temp_db_path

    # Cleanup
    shutil.rmtree(temp_dir)


@pytest.fixture
def session_repo(temp_db):
    """Session repository with temp database."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        return SessionRepository()


@pytest.fixture
def readiness_repo(temp_db):
    """Readiness repository with temp database."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        return ReadinessRepository()


@pytest.fixture
def technique_repo(temp_db):
    """Technique repository with temp database."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        return TechniqueRepository()


@pytest.fixture
def video_repo(temp_db):
    """Video repository with temp database."""
    with patch("rivaflow.config.DB_PATH", temp_db):
        return VideoRepository()


@pytest.fixture
def sample_session_data():
    """Sample session data for testing."""
    return {
        "session_date": date(2025, 1, 20),
        "class_type": "gi",
        "gym_name": "Test Gym",
        "location": "Test City",
        "duration_mins": 60,
        "intensity": 4,
        "rolls": 5,
        "submissions_for": 2,
        "submissions_against": 1,
        "partners": ["Partner1", "Partner2"],
        "techniques": ["armbar", "triangle"],
        "notes": "Good session",
    }


@pytest.fixture
def sample_readiness_data():
    """Sample readiness data for testing."""
    return {
        "check_date": date(2025, 1, 20),
        "sleep": 4,
        "stress": 3,
        "soreness": 2,
        "energy": 4,
        "hotspot_note": "left shoulder",
    }


# ===== User & Authentication Fixtures =====


@pytest.fixture
def test_user(temp_db):
    """Create a test user in the database."""
    user_repo = UserRepository()
    user = user_repo.create(
        email="test@example.com",
        hashed_password=hash_password("testpass123"),
        first_name="Test",
        last_name="User",
    )
    return user


@pytest.fixture
def test_user2(temp_db):
    """Create a second test user for relationship testing."""
    user_repo = UserRepository()
    user = user_repo.create(
        email="test2@example.com",
        hashed_password=hash_password("testpass123"),
        first_name="Test2",
        last_name="User2",
    )
    return user


@pytest.fixture
def auth_token(test_user):
    """Generate a valid JWT token for test_user."""
    return create_access_token(
        data={"sub": str(test_user["id"])}, expires_delta=timedelta(hours=1)
    )


@pytest.fixture
def auth_headers(auth_token):
    """Return Authorization headers with JWT token."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def client(temp_db):
    """FastAPI TestClient with temp database."""
    from fastapi.testclient import TestClient

    from rivaflow.api.main import app

    return TestClient(app)


@pytest.fixture
def authenticated_client(client, auth_headers):
    """TestClient with authentication headers pre-set."""
    client.headers.update(auth_headers)
    return client


# ===== Additional Repository Fixtures =====


@pytest.fixture
def user_repo(temp_db):
    """User repository with temp database."""
    return UserRepository()


@pytest.fixture
def profile_repo(temp_db):
    """Profile repository with temp database."""
    return ProfileRepository()


@pytest.fixture
def friend_repo(temp_db):
    """Friend repository with temp database."""
    return FriendRepository()


# ===== Data Factory Fixtures =====


@pytest.fixture
def session_factory(temp_db, test_user):
    """Factory for creating test sessions."""

    def _create_session(**kwargs):
        defaults = {
            "user_id": test_user["id"],
            "session_date": date.today(),
            "class_type": "gi",
            "gym_name": "Test Gym",
            "location": "Test City",
            "duration_mins": 60,
            "intensity": 4,
            "rolls": 5,
            "submissions_for": 0,
            "submissions_against": 0,
        }
        defaults.update(kwargs)
        repo = SessionRepository()
        return repo.create(**defaults)

    return _create_session


@pytest.fixture
def readiness_factory(temp_db, test_user):
    """Factory for creating test readiness entries."""

    def _create_readiness(**kwargs):
        defaults = {
            "user_id": test_user["id"],
            "check_date": date.today(),
            "sleep": 4,
            "stress": 3,
            "soreness": 2,
            "energy": 4,
        }
        defaults.update(kwargs)
        repo = ReadinessRepository()
        return repo.log_readiness(**defaults)

    return _create_readiness
