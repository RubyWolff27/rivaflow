"""Pytest fixtures for RivaFlow tests."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import date
from unittest.mock import patch

from rivaflow.config import APP_DIR, DB_PATH
from rivaflow.db.database import init_db
from rivaflow.db.repositories import (
    SessionRepository,
    ReadinessRepository,
    TechniqueRepository,
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
