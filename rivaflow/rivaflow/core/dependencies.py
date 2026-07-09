"""FastAPI dependency injection for authentication and services."""

import logging

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError

from rivaflow.core.auth import decode_access_token
from rivaflow.core.exceptions import AuthenticationError, ForbiddenError
from rivaflow.core.utils.cache import get_cache
from rivaflow.db.repositories.api_key_repo import (
    API_KEY_PREFIXES,
    SCOPE_READ,
    ApiKeyRepository,
)
from rivaflow.db.repositories.user_repo import UserRepository

logger = logging.getLogger(__name__)

# User cache TTL — short enough that permission changes propagate quickly
_USER_CACHE_TTL = 60  # seconds

# HTTP Bearer token security scheme — accepts either a JWT (existing) OR an
# API key (`rf_pk_...`). Both arrive in `Authorization: Bearer <value>`; we
# discriminate by the key prefix below.
security = HTTPBearer()


def _load_user_with_cache(user_id: int) -> dict:
    """Resolve a user id → user dict, cached for _USER_CACHE_TTL seconds.

    Shared by both the JWT path and the API key path so subsequent requests
    within the cache window don't re-hit the database.
    """
    cache = get_cache()
    cache_key = f"user:{user_id}"
    from rivaflow.core.utils.cache import _MISSING

    cached_user = cache.get(cache_key)
    if cached_user is not _MISSING:
        return cached_user  # type: ignore[no-any-return]

    user_repo = UserRepository()
    user = user_repo.get_by_id(user_id)

    if user is None:
        raise AuthenticationError(message="User not found")

    if not user.get("is_active"):
        raise AuthenticationError(message="User account is inactive")

    # Strip sensitive fields before caching/returning.
    user.pop("hashed_password", None)

    cache.set(cache_key, user, _USER_CACHE_TTL)
    return user


def _authenticate_api_key(token: str) -> dict:
    """Resolve an `rf_pk_`/`rf_vk_` API key to its owning user.

    Returns a COPY of the cached user annotated with `_auth_scope` (the key's
    scope) — copied because the user cache is shared across requests and
    mutating it would leak one key's scope onto another request.
    """
    try:
        key_hash = ApiKeyRepository.hash_key(token)
        api_key = ApiKeyRepository.get_active_by_hash(key_hash)
        if api_key is None:
            raise AuthenticationError(message="Invalid or revoked API key")

        user = dict(_load_user_with_cache(api_key["user_id"]))
        user["_auth_scope"] = api_key.get("scopes") or "full"

        # Best-effort last-used bump — never fatal to the auth path.
        try:
            ApiKeyRepository.update_last_used(api_key["id"])
        except Exception as bump_err:  # pragma: no cover — non-critical
            logger.warning(
                "update_last_used failed for api_key id=%s: %s",
                api_key["id"],
                bump_err,
            )
        return user
    except AuthenticationError:
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error("API key authentication error: %s", e)
        raise AuthenticationError(message="Authentication failed")


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    Dependency that authenticates either a JWT or an API key from
    `Authorization: Bearer <token>`.

    Discrimination:
        - Token starts with `rf_pk_` → look up `api_keys` by SHA-256 hash,
          confirm not revoked, bump `last_used_at`, return owning user.
        - Otherwise → decode as a short-lived access JWT and load the user.

    Uses a short-lived in-memory cache (post-resolution) so the database is
    not hit on every authenticated request.

    Args:
        credentials: HTTP Authorization credentials (Bearer token).

    Returns:
        User dictionary with id, email, first_name, last_name, etc.

    Raises:
        AuthenticationError: If the credential is invalid, expired, revoked,
        or the user is missing/inactive.
    """
    token = credentials.credentials

    # ── API key path ────────────────────────────────────────────────────────
    if token.startswith(API_KEY_PREFIXES):
        return _authenticate_api_key(token)

    # ── JWT path (existing behaviour) ───────────────────────────────────────
    try:
        payload = decode_access_token(token)
        if payload is None:
            raise AuthenticationError(message="Could not validate credentials")
        user_id_str = payload.get("sub")
        user_id: int = int(user_id_str) if user_id_str else None  # type: ignore[assignment]

        if user_id is None:
            raise AuthenticationError(message="Invalid authentication credentials")

        return _load_user_with_cache(user_id)

    except PyJWTError:
        raise AuthenticationError(message="Could not validate credentials")
    except AuthenticationError:
        raise
    except (ValueError, KeyError, TypeError) as e:
        logger.error("Authentication error: %s", e)
        raise AuthenticationError(message="Authentication failed")


def require_write_scope(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency for mutating routes: reject read-only API keys.

    A read-scoped `rf_vk_` key (minted for the bookmarkable cockpit URL) can
    read every endpoint but must never write. JWT sessions and full `rf_pk_`
    keys carry no read restriction and pass through unchanged.
    """
    if current_user.get("_auth_scope") == SCOPE_READ:
        raise ForbiddenError(
            message="This API key is read-only and cannot perform writes"
        )
    return current_user


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
