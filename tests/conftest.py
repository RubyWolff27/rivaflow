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
# Use PostgreSQL if DATABASE_URL is set (CI), otherwise use SQLite (local)
# Do NOT delete DATABASE_URL - let CI use PostgreSQL

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
    """Create a temporary database for testing.

    Uses PostgreSQL if DATABASE_URL is set (CI), otherwise SQLite (local).
    """
    database_url = os.environ.get("DATABASE_URL")

    if database_url:
        # PostgreSQL mode (CI)
        from rivaflow.db.database import get_connection
        from rivaflow.db.migrate import run_migrations

        # Initialize database schema and run migrations
        init_db()  # Creates migrations tracking table
        try:
            run_migrations()  # Applies all migrations
        except Exception as e:
            # Migrations may already be applied
            print(f"Note: Migrations may already be applied: {e}")

        # Clean all tables before EACH test
        def cleanup_tables():
            try:
                with get_connection() as conn:
                    cursor = conn.cursor()
                    # Get all tables except schema_migrations
                    cursor.execute("""
                        SELECT table_name FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                        AND table_name != 'schema_migrations'
                    """)
                    tables = cursor.fetchall()

                    if tables:
                        # Disable foreign key checks temporarily
                        cursor.execute("SET session_replication_role = 'replica';")
                        # Truncate each table
                        for table_row in tables:
                            # Handle RealDictRow from psycopg2
                            table_name = table_row["table_name"]
                            cursor.execute(
                                f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE'
                            )
                        # Re-enable foreign key checks
                        cursor.execute("SET session_replication_role = 'origin';")
                        conn.commit()
            except Exception as e:
                print(f"Warning: Table cleanup failed: {e}")

        # Clean before test
        cleanup_tables()

        yield database_url

        # Clean after test (for next test)
        cleanup_tables()
    else:
        # SQLite mode (local development)
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
        return repo.upsert(**defaults)

    return _create_readiness
