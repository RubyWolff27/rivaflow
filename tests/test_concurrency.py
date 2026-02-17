"""Tests for concurrent operations — verifies thread safety and data integrity."""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

from rivaflow.core.auth import (
    generate_refresh_token,
    get_refresh_token_expiry,
    hash_password,
)
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.refresh_token_repo import RefreshTokenRepository
from rivaflow.db.repositories.session_repo import SessionRepository
from rivaflow.db.repositories.user_repo import UserRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_user(email="concurrent@example.com"):
    """Create a user for concurrency tests."""
    return UserRepository.create(
        email=email,
        hashed_password=hash_password("testpass123"),
        first_name="Concurrent",
        last_name="Tester",
    )


def _create_session_for_user(user_id, index=0):
    """Create a session and return its ID. Thread-safe via its own connection."""
    repo = SessionRepository()
    session_id = repo.create(
        user_id=user_id,
        session_date=date.today() - timedelta(days=index),
        class_type="gi",
        gym_name=f"Gym-{index}",
        duration_mins=60,
        intensity=4,
        rolls=3,
        submissions_for=1,
        submissions_against=0,
    )
    return session_id


def _get_session_count(user_id):
    """Count sessions for a user."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("SELECT COUNT(*) FROM sessions WHERE user_id = ?"),
            (user_id,),
        )
        row = cursor.fetchone()
        if isinstance(row, dict):
            return list(row.values())[0]
        return row[0]


# ===========================================================================
# Concurrent session creation
# ===========================================================================


class TestConcurrentSessionCreation:
    """Verify multiple threads can create sessions simultaneously."""

    def test_five_threads_create_sessions(self, temp_db):
        user = _make_user("session_concurrent@example.com")
        user_id = user["id"]
        num_threads = 5
        results = []
        errors = []

        def create_one(idx):
            try:
                sid = _create_session_for_user(user_id, index=idx)
                return sid
            except Exception as exc:
                return exc

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            futures = [pool.submit(create_one, i) for i in range(num_threads)]
            for future in as_completed(futures):
                result = future.result()
                if isinstance(result, Exception):
                    errors.append(result)
                else:
                    results.append(result)

        # All 5 sessions should be created without errors
        assert len(errors) == 0, f"Errors during concurrent creation: {errors}"
        assert len(results) == num_threads

        # All session IDs should be unique
        assert len(set(results)) == num_threads

        # Verify count in database
        count = _get_session_count(user_id)
        assert count == num_threads

    def test_concurrent_sessions_have_correct_data(self, temp_db):
        user = _make_user("data_check@example.com")
        user_id = user["id"]
        num_threads = 3

        def create_one(idx):
            try:
                return _create_session_for_user(user_id, index=idx)
            except Exception as exc:
                return exc

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            futures = [pool.submit(create_one, i) for i in range(num_threads)]
            session_ids = []
            for future in as_completed(futures):
                result = future.result()
                assert not isinstance(result, Exception), f"Error: {result}"
                session_ids.append(result)

        # Verify each session has the right user_id and unique gym_name
        repo = SessionRepository()
        gym_names = set()
        for sid in session_ids:
            session = repo.get_by_id(user_id, sid)
            assert session is not None
            assert session["user_id"] == user_id
            gym_names.add(session["gym_name"])

        assert len(gym_names) == num_threads


# ===========================================================================
# Concurrent token refresh (create + delete cycle)
# ===========================================================================


class TestConcurrentTokenRefresh:
    """Simulate concurrent refresh token operations."""

    def test_two_threads_create_tokens_concurrently(self, temp_db):
        user = _make_user("token_user@example.com")
        user_id = user["id"]
        results = []
        errors = []

        def create_token(idx):
            try:
                token_str = generate_refresh_token()
                expires = get_refresh_token_expiry()
                token_record = RefreshTokenRepository.create(
                    user_id=user_id, token=token_str, expires_at=expires
                )
                return token_str, token_record
            except Exception as exc:
                return exc

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(create_token, i) for i in range(2)]
            for future in as_completed(futures):
                result = future.result()
                if isinstance(result, Exception):
                    errors.append(result)
                else:
                    results.append(result)

        assert len(errors) == 0, f"Token creation errors: {errors}"
        assert len(results) == 2

        # Both tokens should exist in the database
        all_tokens = RefreshTokenRepository.get_by_user_id(user_id)
        assert len(all_tokens) == 2

    def test_concurrent_create_and_delete(self, temp_db):
        """One thread creates a token while another deletes old ones."""
        user = _make_user("token_cd@example.com")
        user_id = user["id"]

        # Pre-create a token to be deleted
        old_token = generate_refresh_token()
        RefreshTokenRepository.create(
            user_id=user_id,
            token=old_token,
            expires_at=get_refresh_token_expiry(),
        )

        new_token_str = generate_refresh_token()
        barrier = threading.Barrier(2, timeout=5)
        results = {}
        errors = []

        def delete_old():
            try:
                barrier.wait()
                deleted = RefreshTokenRepository.delete_by_token(old_token)
                results["deleted"] = deleted
            except Exception as exc:
                errors.append(("delete", exc))

        def create_new():
            try:
                barrier.wait()
                record = RefreshTokenRepository.create(
                    user_id=user_id,
                    token=new_token_str,
                    expires_at=get_refresh_token_expiry(),
                )
                results["created"] = record
            except Exception as exc:
                errors.append(("create", exc))

        with ThreadPoolExecutor(max_workers=2) as pool:
            f1 = pool.submit(delete_old)
            f2 = pool.submit(create_new)
            f1.result()
            f2.result()

        assert len(errors) == 0, f"Errors: {errors}"
        assert results.get("deleted") is True
        assert results.get("created") is not None

        # Old token should be gone, new one should exist
        assert RefreshTokenRepository.get_by_token(old_token) is None
        assert RefreshTokenRepository.get_by_token(new_token_str) is not None


# ===========================================================================
# Data integrity after concurrent writes
# ===========================================================================


class TestDataIntegrityAfterConcurrentWrites:
    """Verify no data corruption after concurrent writes."""

    def test_no_duplicate_session_ids(self, temp_db):
        """Each concurrent INSERT should get a unique auto-increment ID."""
        user = _make_user("integrity@example.com")
        user_id = user["id"]
        num_threads = 5

        def create_one(idx):
            return _create_session_for_user(user_id, index=idx)

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            futures = [pool.submit(create_one, i) for i in range(num_threads)]
            ids = [f.result() for f in futures]

        # Every ID must be unique
        assert len(set(ids)) == num_threads

    def test_user_counts_consistent_after_concurrent_inserts(self, temp_db):
        """After concurrent inserts, total count should match thread count."""
        user = _make_user("count_check@example.com")
        user_id = user["id"]
        num_threads = 4

        def create_one(idx):
            return _create_session_for_user(user_id, index=idx)

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            futures = [pool.submit(create_one, i) for i in range(num_threads)]
            for f in futures:
                f.result()  # wait and raise any exceptions

        # Verify via raw SQL
        count = _get_session_count(user_id)
        assert count == num_threads

    def test_concurrent_user_creation(self, temp_db):
        """Multiple users created concurrently should all succeed."""
        num_threads = 3

        def create_user(idx):
            return UserRepository.create(
                email=f"concurrent_{idx}@example.com",
                hashed_password=hash_password("pass123"),
                first_name=f"User{idx}",
                last_name="Concurrent",
            )

        with ThreadPoolExecutor(max_workers=num_threads) as pool:
            futures = [pool.submit(create_user, i) for i in range(num_threads)]
            users = [f.result() for f in futures]

        # All users should have unique IDs and emails
        user_ids = [u["id"] for u in users]
        emails = [u["email"] for u in users]
        assert len(set(user_ids)) == num_threads
        assert len(set(emails)) == num_threads

    def test_session_data_not_corrupted(self, temp_db):
        """Verify that concurrent writes don't mix up fields between sessions."""
        user = _make_user("corruption_check@example.com")
        user_id = user["id"]

        def create_labeled(idx):
            repo = SessionRepository()
            sid = repo.create(
                user_id=user_id,
                session_date=date(2026, 1, 10 + idx),
                class_type="gi" if idx % 2 == 0 else "nogi",
                gym_name=f"Gym-{idx}",
                duration_mins=30 + idx * 10,
                intensity=idx + 1,
                rolls=idx,
                submissions_for=0,
                submissions_against=0,
            )
            return sid, idx

        with ThreadPoolExecutor(max_workers=4) as pool:
            futures = [pool.submit(create_labeled, i) for i in range(4)]
            results = [f.result() for f in futures]

        repo = SessionRepository()
        for sid, idx in results:
            session = repo.get_by_id(user_id, sid)
            assert session is not None
            assert session["gym_name"] == f"Gym-{idx}"
            assert session["intensity"] == idx + 1
            assert session["rolls"] == idx
            expected_type = "gi" if idx % 2 == 0 else "nogi"
            assert session["class_type"] == expected_type
