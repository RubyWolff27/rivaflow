"""Pydantic models for RivaFlow (web-ready for future API)."""

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator


class ClassType(str, Enum):
    """Training class types."""

    GI = "gi"
    NO_GI = "no-gi"
    OPEN_MAT = "open-mat"
    COMPETITION = "competition"
    STRENGTH_CONDITIONING = "s&c"
    CARDIO = "cardio"
    MOBILITY = "mobility"


class VisibilityLevel(str, Enum):
    """Session visibility levels for future sharing."""

    PRIVATE = "private"
    ATTENDANCE = "attendance"
    SUMMARY = "summary"
    FULL = "full"


class SessionRollData(BaseModel):
    """Individual roll data for detailed tracking."""

    roll_number: int = 1
    partner_id: int | None = None
    partner_name: str | None = None
    duration_mins: int | None = None
    submissions_for: list[int] | None = None  # Movement IDs from glossary
    submissions_against: list[int] | None = None  # Movement IDs from glossary
    notes: str | None = None


class MediaUrl(BaseModel):
    """Media URL attachment for technique tracking."""

    type: str  # "video" or "image"
    url: str
    title: str | None = None


class SessionTechniqueCreate(BaseModel):
    """Individual technique data for detailed tracking."""

    movement_id: int
    technique_number: int = 1
    notes: str | None = None
    media_urls: list[MediaUrl] | None = None


class SessionCreate(BaseModel):
    """Input model for creating a session."""

    session_date: date = Field(
        description="Date of the training session (cannot be in the future)"
    )
    class_time: str | None = Field(
        default=None,
        pattern=r"^([01]\d|2[0-3]):([0-5]\d)$",
        description="Start time in 24-hour format (HH:MM). Example: 18:30",
    )
    class_type: ClassType = Field(
        description="Type of training class. Common values: gi, no-gi, open-mat, drilling"
    )
    gym_name: str = Field(
        min_length=1,
        max_length=100,
        description="Name of the gym or academy. Cannot be empty.",
    )
    location: str | None = Field(
        default=None,
        max_length=200,
        description="Optional location (city, address, or area)",
    )
    duration_mins: int = Field(
        default=60,
        ge=1,
        le=480,
        description="Session duration in minutes (1-480). Typical: 60-120 minutes",
    )
    intensity: int = Field(
        default=4,
        ge=1,
        le=5,
        description="Training intensity (1=light, 5=competition pace). Scale of 1-5.",
    )
    rolls: int = Field(default=0, ge=0, description="Number of sparring rounds/rolls")
    submissions_for: int = Field(
        default=0, ge=0, description="Number of submissions you successfully completed"
    )
    submissions_against: int = Field(
        default=0, ge=0, description="Number of times you were submitted"
    )
    partners: list[str] | None = Field(
        default=None, description="List of training partner names"
    )
    techniques: list[str] | None = Field(
        default=None, description="Techniques worked on during the session"
    )
    notes: str | None = Field(
        default=None, description="Personal notes about the session"
    )
    visibility_level: VisibilityLevel = Field(
        default=VisibilityLevel.PRIVATE,
        description="Who can see this session: private, attendance, summary, or full",
    )
    instructor_id: int | None = None
    instructor_name: str | None = None
    session_rolls: list[SessionRollData] | None = None
    session_techniques: list[SessionTechniqueCreate] | None = None
    whoop_strain: float | None = Field(
        default=None, ge=0, le=21, description="WHOOP strain score (0-21)"
    )
    whoop_calories: int | None = Field(
        default=None, ge=0, description="Calories burned (from WHOOP or other tracker)"
    )
    whoop_avg_hr: int | None = Field(
        default=None, ge=0, le=250, description="Average heart rate during session"
    )
    whoop_max_hr: int | None = Field(
        default=None, ge=0, le=250, description="Maximum heart rate during session"
    )
    attacks_attempted: int = Field(
        default=0, ge=0, description="Number of attacks attempted during session"
    )
    attacks_successful: int = Field(
        default=0, ge=0, description="Number of successful attacks during session"
    )
    defenses_attempted: int = Field(
        default=0, ge=0, description="Number of defenses attempted during session"
    )
    defenses_successful: int = Field(
        default=0, ge=0, description="Number of successful defenses during session"
    )

    @field_validator(
        "class_time", "location", "notes", "instructor_name", mode="before"
    )
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty strings to None for optional string fields."""
        if v == "":
            return None
        return v

    @field_validator("partners", "techniques", mode="before")
    @classmethod
    def empty_list_to_none(cls, v):
        """Convert empty lists to None for optional list fields."""
        if v is not None and len(v) == 0:
            return None
        return v

    @field_validator("session_date")
    @classmethod
    def validate_session_date(cls, v):
        """Validate session date is not in the future (with 1-day timezone tolerance)."""
        from datetime import date as date_class
        from datetime import timedelta

        today = date_class.today()

        if v > today + timedelta(days=1):
            raise ValueError(
                f"Session date cannot be in the future. "
                f"You provided {v.strftime('%Y-%m-%d')}, but today is {today.strftime('%Y-%m-%d')}. "
                f"Please use today's date or an earlier date."
            )
        return v

    @field_validator("gym_name")
    @classmethod
    def validate_gym_name(cls, v):
        """Validate gym name is not empty after stripping whitespace."""
        if not v or not v.strip():
            raise ValueError(
                "Gym name cannot be empty. Please provide the name of your training academy or gym."
            )
        return v.strip()

    @model_validator(mode="after")
    def validate_fight_dynamics(self):
        """Validate that successful counts do not exceed attempted counts."""
        if self.attacks_successful > self.attacks_attempted:
            raise ValueError("attacks_successful cannot exceed attacks_attempted")
        if self.defenses_successful > self.defenses_attempted:
            raise ValueError("defenses_successful cannot exceed defenses_attempted")
        return self


class SessionUpdate(BaseModel):
    """Input model for updating a session. All fields optional."""

    session_date: date | None = None
    class_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):([0-5]\d)$")
    class_type: ClassType | None = None
    gym_name: str | None = Field(default=None, min_length=1, max_length=100)
    location: str | None = Field(default=None, max_length=200)
    duration_mins: int | None = Field(default=None, ge=1, le=480)
    intensity: int | None = Field(default=None, ge=1, le=5)
    rolls: int | None = Field(default=None, ge=0)
    submissions_for: int | None = Field(default=None, ge=0)
    submissions_against: int | None = Field(default=None, ge=0)
    partners: list[str] | None = None
    techniques: list[str] | None = None
    notes: str | None = None
    visibility_level: VisibilityLevel | None = None
    instructor_id: int | None = None
    instructor_name: str | None = None
    session_rolls: list[SessionRollData] | None = None
    session_techniques: list[SessionTechniqueCreate] | None = None
    whoop_strain: float | None = Field(default=None, ge=0, le=21)
    whoop_calories: int | None = Field(default=None, ge=0)
    whoop_avg_hr: int | None = Field(default=None, ge=0, le=250)
    whoop_max_hr: int | None = Field(default=None, ge=0, le=250)
    attacks_attempted: int | None = Field(default=None, ge=0)
    attacks_successful: int | None = Field(default=None, ge=0)
    defenses_attempted: int | None = Field(default=None, ge=0)
    defenses_successful: int | None = Field(default=None, ge=0)
    needs_review: bool | None = None

    @field_validator(
        "class_time", "gym_name", "location", "notes", "instructor_name", mode="before"
    )
    @classmethod
    def empty_str_to_none(cls, v):
        """Convert empty strings to None for optional string fields."""
        if v == "":
            return None
        return v

    @model_validator(mode="after")
    def validate_fight_dynamics(self):
        """Validate that successful counts do not exceed attempted counts."""
        if (
            self.attacks_successful is not None
            and self.attacks_attempted is not None
            and self.attacks_successful > self.attacks_attempted
        ):
            raise ValueError("attacks_successful cannot exceed attacks_attempted")
        if (
            self.defenses_successful is not None
            and self.defenses_attempted is not None
            and self.defenses_successful > self.defenses_attempted
        ):
            raise ValueError("defenses_successful cannot exceed defenses_attempted")
        return self


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
    hotspot_note: str | None = None
    weight_kg: float | None = Field(default=None, ge=30, le=300)

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
    category: str | None = None


class Technique(TechniqueCreate):
    """Full technique model with database fields."""

    id: int
    last_trained_date: date | None = None
    created_at: datetime


class VideoTimestamp(BaseModel):
    """Timestamp marker in a video."""

    time: str  # Format: "2:30"
    label: str


class VideoCreate(BaseModel):
    """Input model for creating a video."""

    url: str
    title: str | None = None
    timestamps: list[VideoTimestamp] | None = None
    technique_id: int | None = None


class Video(VideoCreate):
    """Full video model with database fields."""

    id: int
    created_at: datetime
