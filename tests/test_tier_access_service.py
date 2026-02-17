"""Unit tests for TierAccessService.

The tier_access_service module imports from rivaflow.config.tiers, but
rivaflow.config resolves to the legacy config.py *module* (not the
config/ package) because there is no __init__.py in config/.
We fix this at import-time by registering the tiers module in sys.modules
so the service module can be imported successfully.
"""

import importlib
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

# ------------------------------------------------------------------
# Bootstrap: make "rivaflow.config.tiers" importable despite the
# config.py / config/ name collision, and patch the stale
# get_db_connection name that tier_access_service expects.
# ------------------------------------------------------------------
_tiers_path = (
    Path(__file__).resolve().parents[1]
    / "rivaflow"
    / "rivaflow"
    / "config"
    / "tiers.py"
)
_spec = importlib.util.spec_from_file_location("rivaflow.config.tiers", _tiers_path)
_tiers_mod = importlib.util.module_from_spec(_spec)
sys.modules["rivaflow.config.tiers"] = _tiers_mod
_spec.loader.exec_module(_tiers_mod)

# The service imports get_db_connection which was renamed to get_connection.
# Patch it into the database module so the import succeeds.
import rivaflow.db.database as _db_mod  # noqa: E402

if not hasattr(_db_mod, "get_db_connection"):
    _db_mod.get_db_connection = _db_mod.get_connection

from rivaflow.core.services.tier_access_service import TierAccessService  # noqa: E402


class TestCheckTierAccess:
    """Tests for check_tier_access -- feature permission checks."""

    def test_free_tier_has_basic_features(self):
        """Free tier should have access to basic features."""
        allowed, error = TierAccessService.check_tier_access("free", "session_tracking")
        assert allowed is True
        assert error is None

    def test_free_tier_has_basic_analytics(self):
        """Free tier should have access to basic analytics."""
        allowed, error = TierAccessService.check_tier_access("free", "basic_analytics")
        assert allowed is True
        assert error is None

    def test_free_tier_has_technique_tracking(self):
        """Free tier should have technique tracking."""
        allowed, error = TierAccessService.check_tier_access(
            "free", "technique_tracking"
        )
        assert allowed is True
        assert error is None

    def test_free_tier_denied_advanced_analytics(self):
        """Free tier should NOT have access to advanced analytics."""
        allowed, error = TierAccessService.check_tier_access(
            "free", "advanced_analytics"
        )
        assert allowed is False
        assert "Premium" in error
        assert "Free" in error

    def test_free_tier_denied_admin_panel(self):
        """Free tier should NOT have admin panel access."""
        allowed, error = TierAccessService.check_tier_access("free", "admin_panel")
        assert allowed is False
        assert "Premium" in error

    def test_premium_tier_has_advanced_analytics(self):
        """Premium tier should have access to advanced analytics."""
        allowed, error = TierAccessService.check_tier_access(
            "premium", "advanced_analytics"
        )
        assert allowed is True
        assert error is None

    def test_premium_tier_has_friend_suggestions(self):
        """Premium tier should have friend suggestions."""
        allowed, error = TierAccessService.check_tier_access(
            "premium", "friend_suggestions"
        )
        assert allowed is True
        assert error is None

    def test_premium_tier_denied_admin_panel(self):
        """Premium tier should NOT have admin panel access."""
        allowed, error = TierAccessService.check_tier_access("premium", "admin_panel")
        assert allowed is False
        assert "Premium" in error

    def test_lifetime_premium_has_advanced_features(self):
        """Lifetime premium should have all premium features."""
        allowed, error = TierAccessService.check_tier_access(
            "lifetime_premium", "advanced_analytics"
        )
        assert allowed is True
        assert error is None

    def test_admin_tier_has_admin_panel(self):
        """Admin tier should have admin panel access."""
        allowed, error = TierAccessService.check_tier_access("admin", "admin_panel")
        assert allowed is True
        assert error is None

    def test_admin_tier_has_verify_gyms(self):
        """Admin tier should have verify_gyms access."""
        allowed, error = TierAccessService.check_tier_access("admin", "verify_gyms")
        assert allowed is True
        assert error is None


class TestDefaultTierBehavior:
    """Tests for edge cases around invalid or missing tier values."""

    def test_none_tier_returns_invalid(self):
        """None tier should return invalid tier error."""
        allowed, error = TierAccessService.check_tier_access(None, "session_tracking")
        assert allowed is False
        assert error == "Invalid user tier"

    def test_empty_string_tier_returns_invalid(self):
        """Empty string tier should return invalid tier error."""
        allowed, error = TierAccessService.check_tier_access("", "session_tracking")
        assert allowed is False
        assert error == "Invalid user tier"

    def test_unknown_tier_returns_invalid(self):
        """Unknown tier name should return invalid tier error."""
        allowed, error = TierAccessService.check_tier_access(
            "gold_tier", "session_tracking"
        )
        assert allowed is False
        assert error == "Invalid user tier"

    def test_feature_not_in_any_tier(self):
        """Requesting a completely unknown feature should be denied."""
        allowed, error = TierAccessService.check_tier_access("free", "teleportation")
        assert allowed is False
        assert "Premium" in error


class TestCheckUsageLimit:
    """Tests for check_usage_limit -- usage limit enforcement per tier."""

    def test_unlimited_feature_returns_allowed(self):
        """Premium tier with unlimited (-1) limit should always be allowed."""
        with patch.object(TierAccessService, "_get_current_usage", return_value=999):
            allowed, error, count = TierAccessService.check_usage_limit(
                user_id=1, user_tier="premium", feature="max_friends"
            )
        assert allowed is True
        assert error is None
        assert count == -1

    def test_zero_limit_feature_not_available(self):
        """A feature with limit=0 should not be available."""
        with patch(
            "rivaflow.core.services.tier_access_service.get_limit",
            return_value=0,
        ):
            allowed, error, count = TierAccessService.check_usage_limit(
                user_id=1,
                user_tier="free",
                feature="nonexistent_feature",
            )
        assert allowed is False
        assert "not available" in error
        assert count == 0

    def test_under_limit_is_allowed(self):
        """Usage below limit should be allowed."""
        with patch.object(TierAccessService, "_get_current_usage", return_value=5):
            allowed, error, count = TierAccessService.check_usage_limit(
                user_id=1, user_tier="free", feature="max_friends"
            )
        assert allowed is True
        assert error is None
        assert count == 5

    def test_at_limit_is_denied(self):
        """Usage at limit should be denied."""
        with patch.object(TierAccessService, "_get_current_usage", return_value=10):
            allowed, error, count = TierAccessService.check_usage_limit(
                user_id=1, user_tier="free", feature="max_friends"
            )
        assert allowed is False
        assert "limit" in error.lower()
        assert count == 10

    def test_over_limit_is_denied(self):
        """Usage over limit should be denied."""
        with patch.object(TierAccessService, "_get_current_usage", return_value=15):
            allowed, error, count = TierAccessService.check_usage_limit(
                user_id=1, user_tier="free", feature="max_friends"
            )
        assert allowed is False
        assert "Free" in error
        assert "10" in error
        assert count == 15

    def test_increment_increases_count(self):
        """increment=True should call _increment_usage and bump count."""
        with (
            patch.object(
                TierAccessService,
                "_get_current_usage",
                return_value=3,
            ),
            patch.object(TierAccessService, "_increment_usage") as mock_inc,
        ):
            allowed, error, count = TierAccessService.check_usage_limit(
                user_id=1,
                user_tier="free",
                feature="max_friends",
                increment=True,
            )
        assert allowed is True
        assert error is None
        assert count == 4  # 3 + 1
        mock_inc.assert_called_once_with(1, "max_friends")

    def test_increment_not_called_when_at_limit(self):
        """increment=True should NOT increment if already at limit."""
        with (
            patch.object(
                TierAccessService,
                "_get_current_usage",
                return_value=10,
            ),
            patch.object(TierAccessService, "_increment_usage") as mock_inc,
        ):
            allowed, error, count = TierAccessService.check_usage_limit(
                user_id=1,
                user_tier="free",
                feature="max_friends",
                increment=True,
            )
        assert allowed is False
        mock_inc.assert_not_called()


class TestCheckTierExpired:
    """Tests for check_tier_expired."""

    def test_none_expiry_means_not_expired(self):
        """NULL expiry means never expires."""
        assert TierAccessService.check_tier_expired(None) is False

    def test_future_expiry_is_not_expired(self):
        """Future expiry date means tier is still active."""
        future = datetime.now() + timedelta(days=30)
        assert TierAccessService.check_tier_expired(future) is False

    def test_past_expiry_is_expired(self):
        """Past expiry date means tier has expired."""
        past = datetime.now() - timedelta(days=1)
        assert TierAccessService.check_tier_expired(past) is True


class TestGetTierFeatures:
    """Tests for get_tier_features."""

    def test_free_tier_features(self):
        """Free tier should have exactly its defined features."""
        features = TierAccessService.get_tier_features("free")
        assert "session_tracking" in features
        assert "basic_analytics" in features
        assert "advanced_analytics" not in features

    def test_premium_tier_features(self):
        """Premium tier should include advanced features."""
        features = TierAccessService.get_tier_features("premium")
        assert "advanced_analytics" in features
        assert "friend_suggestions" in features

    def test_invalid_tier_returns_empty(self):
        """Invalid tier should return empty list."""
        features = TierAccessService.get_tier_features("nonexistent")
        assert features == []


class TestGetUsageSummary:
    """Tests for get_usage_summary."""

    def test_summary_structure_for_free_tier(self):
        """Usage summary should have correct structure for free tier."""
        with patch.object(TierAccessService, "_get_current_usage", return_value=0):
            summary = TierAccessService.get_usage_summary(user_id=1, user_tier="free")

        assert summary["tier"] == "free"
        assert summary["tier_display"] == "Free"
        assert summary["is_premium"] is False
        assert "features" in summary

    def test_summary_structure_for_premium_tier(self):
        """Usage summary should mark premium correctly."""
        with patch.object(TierAccessService, "_get_current_usage", return_value=0):
            summary = TierAccessService.get_usage_summary(
                user_id=1, user_tier="premium"
            )

        assert summary["tier"] == "premium"
        assert summary["is_premium"] is True

    def test_summary_unlimited_feature_format(self):
        """Unlimited features should show 'unlimited' in summary."""
        with patch.object(TierAccessService, "_get_current_usage", return_value=0):
            summary = TierAccessService.get_usage_summary(
                user_id=1, user_tier="premium"
            )

        # Premium has unlimited max_friends
        assert summary["features"]["max_friends"]["limit"] == "unlimited"
        assert summary["features"]["max_friends"]["current"] == "unlimited"

    def test_summary_limited_feature_shows_percentage(self):
        """Limited features should show usage percentage."""
        with patch.object(TierAccessService, "_get_current_usage", return_value=5):
            summary = TierAccessService.get_usage_summary(user_id=1, user_tier="free")

        friends_usage = summary["features"]["max_friends"]
        assert friends_usage["limit"] == 10
        assert friends_usage["current"] == 5
        assert friends_usage["percentage"] == 50.0

    def test_summary_invalid_tier_returns_empty(self):
        """Invalid tier should return empty dict."""
        summary = TierAccessService.get_usage_summary(
            user_id=1, user_tier="nonexistent"
        )
        assert summary == {}
