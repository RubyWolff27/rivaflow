"""Pydantic response models for FastAPI endpoints.

These models document the shape of API responses and enable automatic
validation/serialization via FastAPI's ``response_model`` parameter.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict

# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


class AuthUser(BaseModel):
    """Minimal user dict returned inside auth responses."""

    model_config = ConfigDict(extra="allow")

    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None


class TokenResponse(BaseModel):
    """Response for login / register."""

    model_config = ConfigDict(extra="allow")

    access_token: str
    token_type: str = "bearer"
    user: AuthUser


class AccessTokenResponse(BaseModel):
    """Response for token refresh."""

    model_config = ConfigDict(extra="allow")

    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    """Response for GET /auth/me."""

    model_config = ConfigDict(extra="allow")

    id: int
    email: str
    first_name: str | None = None
    last_name: str | None = None


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str


# ---------------------------------------------------------------------------
# Sessions
# ---------------------------------------------------------------------------


class SessionResponse(BaseModel):
    """Single training session."""

    model_config = ConfigDict(extra="allow")

    id: int
    user_id: int
    session_date: str | date
    class_type: str
    gym_name: str
    duration_mins: int | None = None
    intensity: int | None = None
    rolls: int | None = None
    submissions_for: int | None = None
    submissions_against: int | None = None
    notes: str | None = None
    class_time: str | None = None
    location: str | None = None
    partners: str | list | None = None
    techniques: str | list | None = None
    visibility_level: str | None = None
    instructor_id: int | None = None
    instructor_name: str | None = None
    whoop_strain: float | None = None
    whoop_calories: float | None = None
    whoop_avg_hr: int | None = None
    whoop_max_hr: int | None = None
    attacks_attempted: int | None = None
    attacks_successful: int | None = None
    defenses_attempted: int | None = None
    defenses_successful: int | None = None
    session_score: float | None = None
    score_breakdown: str | dict | None = None
    score_version: int | None = None
    needs_review: bool | None = None
    navigation: dict | None = None


class SessionScoreResponse(BaseModel):
    """Response for GET /sessions/{id}/score."""

    session_id: int
    session_score: float | None = None
    score_breakdown: dict | str | None = None
    score_version: int | None = None


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class ProfileResponse(BaseModel):
    """User profile."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    user_id: int | None = None
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: str | None = None
    age: int | None = None
    sex: str | None = None
    city: str | None = None
    state: str | None = None
    default_gym: str | None = None
    default_location: str | None = None
    current_grade: str | None = None
    current_professor: str | None = None
    current_instructor_id: int | None = None
    primary_training_type: str | None = None
    height_cm: int | None = None
    target_weight_kg: float | None = None
    target_weight_date: str | None = None
    weekly_sessions_target: int | None = None
    weekly_hours_target: float | None = None
    weekly_rolls_target: int | None = None
    weekly_bjj_sessions_target: int | None = None
    weekly_sc_sessions_target: int | None = None
    weekly_mobility_sessions_target: int | None = None
    show_streak_on_dashboard: bool | None = None
    show_weekly_goals: bool | None = None
    timezone: str | None = None
    avatar_url: str | None = None
    primary_gym_id: int | None = None
    activity_visibility: str | None = None


# ---------------------------------------------------------------------------
# Readiness
# ---------------------------------------------------------------------------


class ReadinessResponse(BaseModel):
    """Single readiness entry."""

    model_config = ConfigDict(extra="allow")

    id: int | None = None
    user_id: int | None = None
    check_date: str | date | None = None
    sleep: int | None = None
    stress: int | None = None
    soreness: int | None = None
    energy: int | None = None
    hotspot_note: str | None = None
    weight_kg: float | None = None


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------


class GoalDimensionProgress(BaseModel):
    """Progress on a single goal dimension (sessions, hours, rolls)."""

    model_config = ConfigDict(extra="allow")

    target: int | float | None = None
    current: int | float | None = None
    percentage: float | None = None
    completed: bool | None = None


class WeeklyGoalProgress(BaseModel):
    """Current week goal progress."""

    model_config = ConfigDict(extra="allow")

    sessions: GoalDimensionProgress | None = None
    hours: GoalDimensionProgress | None = None
    rolls: GoalDimensionProgress | None = None
    days_remaining: int | None = None
    week_start: str | None = None
    week_end: str | None = None


class GoalsSummaryResponse(BaseModel):
    """Comprehensive goals summary."""

    model_config = ConfigDict(extra="allow")

    current_week: dict | None = None
    streaks: dict | None = None
    trend: list | None = None
