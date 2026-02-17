"""Tests for AdminService — admin dashboard operations."""

from datetime import date, timedelta

import pytest

from rivaflow.core.auth import hash_password
from rivaflow.core.services.admin_service import AdminService
from rivaflow.db.database import convert_query, get_connection
from rivaflow.db.repositories.user_repo import UserRepository

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _clear_seed_user():
    """Remove the seed user (id=1, email=user@localhost) created by migrations.

    Migration 002 creates profile id=1, then migration 018 seeds a user from it.
    This helper removes it so tests start with a clean users table.
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("DELETE FROM users WHERE email = ?"),
            ("user@localhost",),
        )
        conn.commit()


def _make_admin(email="admin@example.com"):
    """Create a user and promote them to admin. Returns user dict."""
    user = UserRepository.create(
        email=email,
        hashed_password=hash_password("adminpass123"),
        first_name="Admin",
        last_name="User",
    )
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query("UPDATE users SET is_admin = ? WHERE id = ?"),
            (True, user["id"]),
        )
        conn.commit()
    # Re-fetch to get updated is_admin
    return UserRepository.get_by_id(user["id"])


def _make_user(email="regular@example.com", first_name="Regular", last_name="User"):
    """Create a plain (non-admin) user."""
    return UserRepository.create(
        email=email,
        hashed_password=hash_password("userpass123"),
        first_name=first_name,
        last_name=last_name,
    )


def _insert_session(user_id, session_date=None):
    """Insert a minimal session row."""
    if session_date is None:
        session_date = str(date.today())
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "INSERT INTO sessions (user_id, session_date, class_type, "
                "gym_name, duration_mins, intensity, rolls, "
                "submissions_for, submissions_against) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
            ),
            (user_id, str(session_date), "gi", "Test Gym", 60, 4, 3, 1, 0),
        )
        conn.commit()


def _insert_comment(user_id, activity_id=1, text="Nice session!"):
    """Insert a comment into activity_comments."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "INSERT INTO activity_comments "
                "(user_id, activity_type, activity_id, comment_text) "
                "VALUES (?, ?, ?, ?)"
            ),
            (user_id, "session", activity_id, text),
        )
        conn.commit()


def _insert_relationship(follower_id, following_id):
    """Insert a follow relationship."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "INSERT INTO user_relationships "
                "(follower_user_id, following_user_id) VALUES (?, ?)"
            ),
            (follower_id, following_id),
        )
        conn.commit()


# ===========================================================================
# get_dashboard_stats
# ===========================================================================


class TestGetDashboardStats:
    """AdminService.get_dashboard_stats()"""

    def test_empty_database(self, temp_db):
        _clear_seed_user()
        stats = AdminService.get_dashboard_stats()
        assert stats["total_users"] == 0
        assert stats["active_users"] == 0
        assert stats["new_users_week"] == 0
        assert stats["total_sessions"] == 0
        assert stats["total_comments"] == 0

    def test_counts_users(self, temp_db):
        _clear_seed_user()
        _make_user("u1@example.com")
        _make_user("u2@example.com")
        stats = AdminService.get_dashboard_stats()
        assert stats["total_users"] == 2

    def test_active_users_counted_by_recent_sessions(self, temp_db):
        _clear_seed_user()
        u1 = _make_user("u1@example.com")
        u2 = _make_user("u2@example.com")
        # u1 has a recent session
        _insert_session(u1["id"], date.today())
        # u2 has a session older than 30 days
        _insert_session(u2["id"], date.today() - timedelta(days=31))
        stats = AdminService.get_dashboard_stats()
        assert stats["active_users"] == 1

    def test_new_users_this_week(self, temp_db):
        _clear_seed_user()
        _make_user("new1@example.com")
        stats = AdminService.get_dashboard_stats()
        assert stats["new_users_week"] >= 1

    def test_total_sessions(self, temp_db):
        u = _make_user("u@example.com")
        _insert_session(u["id"])
        _insert_session(u["id"])
        stats = AdminService.get_dashboard_stats()
        assert stats["total_sessions"] == 2

    def test_total_comments(self, temp_db):
        u = _make_user("u@example.com")
        _insert_comment(u["id"], 999, "Comment 1")
        _insert_comment(u["id"], 998, "Comment 2")
        stats = AdminService.get_dashboard_stats()
        assert stats["total_comments"] == 2


# ===========================================================================
# list_users
# ===========================================================================


class TestListUsers:
    """AdminService.list_users()"""

    def test_returns_structure(self, temp_db):
        result = AdminService.list_users()
        assert "users" in result
        assert "total" in result
        assert "limit" in result
        assert "offset" in result

    def test_lists_all_users(self, temp_db):
        _clear_seed_user()
        _make_user("a@example.com")
        _make_user("b@example.com")
        result = AdminService.list_users()
        assert result["total"] == 2
        assert len(result["users"]) == 2

    def test_search_by_email(self, temp_db):
        _make_user("alice@example.com", first_name="Alice")
        _make_user("bob@example.com", first_name="Bob")
        result = AdminService.list_users(search="alice")
        assert result["total"] == 1
        assert result["users"][0]["email"] == "alice@example.com"

    def test_search_by_first_name(self, temp_db):
        _make_user("a@example.com", first_name="Zara")
        _make_user("b@example.com", first_name="Yuki")
        result = AdminService.list_users(search="Zara")
        assert result["total"] == 1

    def test_filter_is_active(self, temp_db):
        _clear_seed_user()
        u = _make_user("inactive@example.com")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("UPDATE users SET is_active = ? WHERE id = ?"),
                (False, u["id"]),
            )
            conn.commit()
        _make_user("active@example.com")
        result = AdminService.list_users(is_active=True)
        assert result["total"] == 1

    def test_filter_is_admin(self, temp_db):
        _clear_seed_user()
        _make_admin("admin@example.com")
        _make_user("regular@example.com")
        result = AdminService.list_users(is_admin=True)
        assert result["total"] == 1

    def test_pagination_limit(self, temp_db):
        _clear_seed_user()
        for i in range(5):
            _make_user(f"u{i}@example.com")
        result = AdminService.list_users(limit=2, offset=0)
        assert len(result["users"]) == 2
        assert result["total"] == 5

    def test_pagination_offset(self, temp_db):
        _clear_seed_user()
        for i in range(5):
            _make_user(f"u{i}@example.com")
        result = AdminService.list_users(limit=2, offset=3)
        assert len(result["users"]) == 2
        assert result["total"] == 5


# ===========================================================================
# get_user_details
# ===========================================================================


class TestGetUserDetails:
    """AdminService.get_user_details()"""

    def test_returns_none_for_missing_user(self, temp_db):
        result = AdminService.get_user_details(99999)
        assert result is None

    def test_returns_user_with_stats(self, temp_db):
        u = _make_user("detail@example.com")
        result = AdminService.get_user_details(u["id"])
        assert result is not None
        assert result["email"] == "detail@example.com"
        assert "stats" in result
        assert result["stats"]["sessions"] == 0
        assert result["stats"]["comments"] == 0
        assert result["stats"]["followers"] == 0
        assert result["stats"]["following"] == 0

    def test_excludes_hashed_password(self, temp_db):
        u = _make_user("safe@example.com")
        result = AdminService.get_user_details(u["id"])
        assert "hashed_password" not in result

    def test_session_count(self, temp_db):
        u = _make_user("s@example.com")
        _insert_session(u["id"])
        _insert_session(u["id"])
        result = AdminService.get_user_details(u["id"])
        assert result["stats"]["sessions"] == 2

    def test_comment_count(self, temp_db):
        u = _make_user("c@example.com")
        _insert_comment(u["id"], 1, "first")
        _insert_comment(u["id"], 2, "second")
        result = AdminService.get_user_details(u["id"])
        assert result["stats"]["comments"] == 2

    def test_follower_following_counts(self, temp_db):
        u1 = _make_user("u1@example.com")
        u2 = _make_user("u2@example.com")
        u3 = _make_user("u3@example.com")
        # u2 and u3 follow u1
        _insert_relationship(u2["id"], u1["id"])
        _insert_relationship(u3["id"], u1["id"])
        # u1 follows u2
        _insert_relationship(u1["id"], u2["id"])

        result = AdminService.get_user_details(u1["id"])
        assert result["stats"]["followers"] == 2
        assert result["stats"]["following"] == 1


# ===========================================================================
# update_user
# ===========================================================================


class TestUpdateUser:
    """AdminService.update_user()"""

    def test_update_is_admin(self, temp_db):
        u = _make_user("upd@example.com")
        result = AdminService.update_user(u["id"], {"is_admin": True})
        assert result is not None
        # is_admin may be stored as int in SQLite; check truthy
        assert result["is_admin"]

    def test_update_subscription_tier(self, temp_db):
        u = _make_user("tier@example.com")
        result = AdminService.update_user(u["id"], {"subscription_tier": "pro"})
        assert result["subscription_tier"] == "pro"

    def test_update_is_beta_user(self, temp_db):
        u = _make_user("beta@example.com")
        result = AdminService.update_user(u["id"], {"is_beta_user": True})
        # SQLite may store as int; check truthy
        assert result["is_beta_user"]

    def test_update_is_active(self, temp_db):
        u = _make_user("act@example.com")
        result = AdminService.update_user(u["id"], {"is_active": False})
        assert not result["is_active"]

    def test_invalid_field_raises(self, temp_db):
        u = _make_user("inv@example.com")
        with pytest.raises(ValueError, match="Invalid field"):
            AdminService.update_user(u["id"], {"email": "hacker@evil.com"})

    def test_empty_changes_returns_user(self, temp_db):
        u = _make_user("noop@example.com")
        result = AdminService.update_user(u["id"], {})
        assert result is not None
        assert result["email"] == "noop@example.com"

    def test_returns_none_for_missing_user(self, temp_db):
        result = AdminService.update_user(99999, {"is_admin": True})
        # update_user returns get_by_id result which is None for missing
        assert result is None


# ===========================================================================
# delete_user
# ===========================================================================


class TestDeleteUser:
    """AdminService.delete_user() — hard delete."""

    def test_deletes_existing_user(self, temp_db):
        u = _make_user("del@example.com")
        assert AdminService.delete_user(u["id"]) is True
        assert UserRepository.get_by_id(u["id"]) is None

    def test_returns_false_for_missing_user(self, temp_db):
        assert AdminService.delete_user(99999) is False


# ===========================================================================
# get_broadcast_users
# ===========================================================================


class TestGetBroadcastUsers:
    """AdminService.get_broadcast_users()"""

    def test_empty_database(self, temp_db):
        _clear_seed_user()
        result = AdminService.get_broadcast_users()
        assert result == []

    def test_returns_active_users_only(self, temp_db):
        _clear_seed_user()
        _make_user("active@example.com")
        inactive = _make_user("inactive@example.com")
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                convert_query("UPDATE users SET is_active = ? WHERE id = ?"),
                (False, inactive["id"]),
            )
            conn.commit()

        result = AdminService.get_broadcast_users()
        assert len(result) == 1
        assert result[0]["email"] == "active@example.com"

    def test_returns_required_fields(self, temp_db):
        _clear_seed_user()
        _make_user("fields@example.com", first_name="Tester")
        result = AdminService.get_broadcast_users()
        assert len(result) == 1
        user = result[0]
        assert "id" in user
        assert "email" in user
        assert "first_name" in user
        assert user["first_name"] == "Tester"
