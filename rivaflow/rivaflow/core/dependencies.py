"""FastAPI dependency injection for authentication and services."""

import logging

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError

from rivaflow.core.auth import decode_access_token
from rivaflow.core.exceptions import AuthenticationError, ForbiddenError
from rivaflow.core.utils.cache import get_cache
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# User cache TTL — short enough that permission changes propagate quickly
_USER_CACHE_TTL = 60  # seconds

# HTTP Bearer token security scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency to extract and validate JWT token from Authorization header.

    Uses a short-lived in-memory cache to avoid hitting the database
    on every single authenticated request.

    Args:
        credentials: HTTP Authorization credentials (Bearer token)

    Returns:
        User dictionary with id, email, first_name, last_name, etc.

    Raises:
        AuthenticationError: If token is invalid, expired, or user not found
    """
    token = credentials.credentials

    try:
        # Decode JWT token
        payload = decode_access_token(token)
        if payload is None:
            raise AuthenticationError(message="Could not validate credentials")
        user_id_str = payload.get("sub")
        user_id: int = int(user_id_str) if user_id_str else None

        if user_id is None:
            raise AuthenticationError(message="Invalid authentication credentials")

        # Check cache first
        cache = get_cache()
        cache_key = f"user:{user_id}"
        from rivaflow.core.utils.cache import _MISSING

        cached_user = cache.get(cache_key)
        if cached_user is not _MISSING:
            return cached_user

        # Cache miss — fetch from database
        user_repo = UserRepository()
        user = user_repo.get_by_id(user_id)

        if user is None:
            raise AuthenticationError(message="User not found")

        # Check if user is active
        if not user.get("is_active"):
            raise AuthenticationError(message="User account is inactive")

        # Remove sensitive fields
        user.pop("hashed_password", None)

        # Cache the user for subsequent requests
        cache.set(cache_key, user, _USER_CACHE_TTL)

        return user

    except PyJWTError:
        raise AuthenticationError(message="Could not validate credentials")
    except AuthenticationError:
        raise
    except (ValueError, KeyError, TypeError) as e:
        # Log unexpected errors and return generic 401
        logger.error(f"Authentication error: {e}")
        raise AuthenticationError(message="Authentication failed")


def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    """
    Dependency that ensures the current user is an admin.

    Use this dependency on admin-only endpoints to restrict access.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        Admin user dictionary

    Raises:
        ForbiddenError: If user is not an admin
    """
    if not current_user.get("is_admin"):
        logger.warning(
            f"Non-admin user {current_user.get('email')} attempted to access admin endpoint"
        )
        raise ForbiddenError(
            message="Admin access required. This incident will be logged."
        )
    return current_user


# ---------------------------------------------------------------------------
# Service provider functions for Depends() injection
# ---------------------------------------------------------------------------


def get_session_service():
    """Provide a SessionService instance."""
    from rivaflow.core.services.session_service import SessionService

    return SessionService()


def get_analytics_service():
    """Provide an AnalyticsService instance."""
    from rivaflow.core.services.analytics_service import AnalyticsService

    return AnalyticsService()


def get_goals_service():
    """Provide a GoalsService instance."""
    from rivaflow.core.services.goals_service import GoalsService

    return GoalsService()


def get_social_service():
    """Provide a SocialService instance."""
    from rivaflow.core.services.social_service import SocialService

    return SocialService()


def get_profile_service():
    """Provide a ProfileService instance."""
    from rivaflow.core.services.profile_service import ProfileService

    return ProfileService()


def get_auth_service():
    """Provide an AuthService instance."""
    from rivaflow.core.services.auth_service import AuthService

    return AuthService()


def get_chat_service():
    """Provide a ChatService instance."""
    from rivaflow.core.services.chat_service import ChatService

    return ChatService()


def get_checkin_service():
    """Provide a CheckinService instance."""
    from rivaflow.core.services.checkin_service import CheckinService

    return CheckinService()


def get_streak_service():
    """Provide a StreakService instance."""
    from rivaflow.core.services.streak_service import StreakService

    return StreakService()


def get_friend_service():
    """Provide a FriendService instance."""
    from rivaflow.core.services.friend_service import FriendService

    return FriendService()


def get_feed_service():
    """Provide a FeedService instance."""
    from rivaflow.core.services.feed_service import FeedService

    return FeedService()


def get_user_service():
    """Provide a UserService instance."""
    from rivaflow.core.services.user_service import UserService

    return UserService()


def get_glossary_service():
    """Provide a GlossaryService instance."""
    from rivaflow.core.services.glossary_service import GlossaryService

    return GlossaryService()


def get_milestone_service():
    """Provide a MilestoneService instance."""
    from rivaflow.core.services.milestone_service import MilestoneService

    return MilestoneService()


def get_events_service():
    """Provide an EventsService instance."""
    from rivaflow.core.services.events_service import EventsService

    return EventsService()


def get_photo_service():
    """Provide a PhotoService instance."""
    from rivaflow.core.services.photo_service import PhotoService

    return PhotoService()


def get_whoop_service():
    """Provide a WhoopService instance."""
    from rivaflow.core.services.whoop_service import WhoopService

    return WhoopService()


def get_notification_service():
    """Provide a NotificationService instance."""
    from rivaflow.core.services.notification_service import NotificationService

    return NotificationService()


def get_grading_service():
    """Provide a GradingService instance."""
    from rivaflow.core.services.grading_service import GradingService

    return GradingService()


def get_readiness_service():
    """Provide a ReadinessService instance."""
    from rivaflow.core.services.readiness_service import ReadinessService

    return ReadinessService()


def get_training_goals_service():
    """Provide a TrainingGoalsService instance."""
    from rivaflow.core.services.training_goals_service import TrainingGoalsService

    return TrainingGoalsService()


def get_feedback_service():
    """Provide a FeedbackService instance."""
    from rivaflow.core.services.feedback_service import FeedbackService

    return FeedbackService()


def get_groups_service():
    """Provide a GroupsService instance."""
    from rivaflow.core.services.groups_service import GroupsService

    return GroupsService()


def get_gym_service():
    """Provide a GymService instance."""
    from rivaflow.core.services.gym_service import GymService

    return GymService()


def get_suggestion_engine():
    """Provide a SuggestionEngine instance."""
    from rivaflow.core.services.suggestion_engine import SuggestionEngine

    return SuggestionEngine()


def get_admin_service():
    """Provide an AdminService instance."""
    from rivaflow.core.services.admin_service import AdminService

    return AdminService()


def get_audit_service():
    """Provide an AuditService instance."""
    from rivaflow.core.services.audit_service import AuditService

    return AuditService()


def get_waitlist_service():
    """Provide a WaitlistService instance."""
    from rivaflow.core.services.waitlist_service import WaitlistService

    return WaitlistService()


def get_email_service():
    """Provide an EmailService instance."""
    from rivaflow.core.services.email_service import EmailService

    return EmailService()


def get_report_service():
    """Provide a ReportService instance."""
    from rivaflow.core.services.report_service import ReportService

    return ReportService()


def get_privacy_service():
    """Provide a PrivacyService instance."""
    from rivaflow.core.services.privacy_service import PrivacyService

    return PrivacyService()


def get_friend_suggestions_service():
    """Provide a FriendSuggestionsService instance."""
    from rivaflow.core.services.friend_suggestions_service import (
        FriendSuggestionsService,
    )

    return FriendSuggestionsService()


def get_rest_service():
    """Provide a RestService instance."""
    from rivaflow.core.services.rest_service import RestService

    return RestService()


def get_video_service():
    """Provide a VideoService instance."""
    from rivaflow.core.services.video_service import VideoService

    return VideoService()


def get_coach_preferences_service():
    """Provide a CoachPreferencesService instance."""
    from rivaflow.core.services.coach_preferences_service import (
        CoachPreferencesService,
    )

    return CoachPreferencesService()


def get_fight_dynamics_service():
    """Provide a FightDynamicsService instance."""
    from rivaflow.core.services.fight_dynamics_service import (
        FightDynamicsService,
    )

    return FightDynamicsService()


def get_whoop_analytics_engine():
    """Provide a WhoopAnalyticsEngine instance."""
    from rivaflow.core.services.whoop_analytics_engine import (
        WhoopAnalyticsEngine,
    )

    return WhoopAnalyticsEngine()
