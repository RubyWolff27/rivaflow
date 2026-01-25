"""Pydantic models for RivaFlow (web-ready for future API)."""
from pydantic import BaseModel, Field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class ClassType(str, Enum):
    """Training class types."""

    GI = "gi"
    NO_GI = "no-gi"
    WRESTLING = "wrestling"
    JUDO = "judo"
    OPEN_MAT = "open-mat"
    STRENGTH_CONDITIONING = "s&c"
    MOBILITY = "mobility"
    YOGA = "yoga"
    REHAB = "rehab"
    PHYSIO = "physio"
    DRILLING = "drilling"


class VisibilityLevel(str, Enum):
    """Session visibility levels for future sharing."""

    PRIVATE = "private"
    ATTENDANCE = "attendance"
    SUMMARY = "summary"
    FULL = "full"


class SessionRollData(BaseModel):
    """Individual roll data for detailed tracking."""

    roll_number: int = 1
    partner_id: Optional[int] = None
    partner_name: Optional[str] = None
    duration_mins: Optional[int] = None
    submissions_for: Optional[list[int]] = None  # Movement IDs from glossary
    submissions_against: Optional[list[int]] = None  # Movement IDs from glossary
    notes: Optional[str] = None


class SessionCreate(BaseModel):
    """Input model for creating a session."""

    session_date: date
    class_type: ClassType
    gym_name: str = Field(min_length=1, max_length=100)
    location: Optional[str] = Field(default=None, max_length=200)
    duration_mins: int = Field(default=60, ge=1, le=480)
    intensity: int = Field(default=4, ge=1, le=5)
    rolls: int = Field(default=0, ge=0)
    submissions_for: int = Field(default=0, ge=0)
    submissions_against: int = Field(default=0, ge=0)
    partners: Optional[list[str]] = None
    techniques: Optional[list[str]] = None
    notes: Optional[str] = None
    visibility_level: VisibilityLevel = VisibilityLevel.PRIVATE
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    session_rolls: Optional[list[SessionRollData]] = None
    whoop_strain: Optional[float] = Field(default=None, ge=0, le=21)
    whoop_calories: Optional[int] = Field(default=None, ge=0)
    whoop_avg_hr: Optional[int] = Field(default=None, ge=0, le=250)
    whoop_max_hr: Optional[int] = Field(default=None, ge=0, le=250)


class SessionUpdate(BaseModel):
    """Input model for updating a session. All fields optional."""

    session_date: Optional[date] = None
    class_type: Optional[ClassType] = None
    gym_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    location: Optional[str] = Field(default=None, max_length=200)
    duration_mins: Optional[int] = Field(default=None, ge=1, le=480)
    intensity: Optional[int] = Field(default=None, ge=1, le=5)
    rolls: Optional[int] = Field(default=None, ge=0)
    submissions_for: Optional[int] = Field(default=None, ge=0)
    submissions_against: Optional[int] = Field(default=None, ge=0)
    partners: Optional[list[str]] = None
    techniques: Optional[list[str]] = None
    notes: Optional[str] = None
    visibility_level: Optional[VisibilityLevel] = None
    instructor_id: Optional[int] = None
    instructor_name: Optional[str] = None
    whoop_strain: Optional[float] = Field(default=None, ge=0, le=21)
    whoop_calories: Optional[int] = Field(default=None, ge=0)
    whoop_avg_hr: Optional[int] = Field(default=None, ge=0, le=250)
    whoop_max_hr: Optional[int] = Field(default=None, ge=0, le=250)


class Session(SessionCreate):
    """Full session model with database fields."""

    id: int
    created_at: datetime
    updated_at: datetime


class ReadinessCreate(BaseModel):
    """Input model for readiness check-in."""

    check_date: date
    sleep: int = Field(ge=1, le=5)
    stress: int = Field(ge=1, le=5)
    soreness: int = Field(ge=1, le=5)
    energy: int = Field(ge=1, le=5)
    hotspot_note: Optional[str] = None

    @property
    def composite_score(self) -> int:
        """Calculate composite readiness score (4-20 range, higher is better)."""
        return self.sleep + (6 - self.stress) + (6 - self.soreness) + self.energy


class Readiness(ReadinessCreate):
    """Full readiness model with database fields."""

    id: int
    created_at: datetime
    updated_at: datetime


class TechniqueCreate(BaseModel):
    """Input model for creating a technique."""

    name: str = Field(min_length=1, max_length=100)
    category: Optional[str] = None


class Technique(TechniqueCreate):
    """Full technique model with database fields."""

    id: int
    last_trained_date: Optional[date] = None
    created_at: datetime


class VideoTimestamp(BaseModel):
    """Timestamp marker in a video."""

    time: str  # Format: "2:30"
    label: str


class VideoCreate(BaseModel):
    """Input model for creating a video."""

    url: str
    title: Optional[str] = None
    timestamps: Optional[list[VideoTimestamp]] = None
    technique_id: Optional[int] = None


class Video(VideoCreate):
    """Full video model with database fields."""

    id: int
    created_at: datetime
