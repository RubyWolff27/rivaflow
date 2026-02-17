"""Application-wide constants for RivaFlow.

This module centralizes magic strings and configuration values used throughout the application.
"""

# ==============================================================================
# SORTING AND ORDERING
# ==============================================================================

# Grading sort options (whitelist for SQL injection protection)
GRADING_SORT_OPTIONS = {
    "date_graded ASC",
    "date_graded DESC",
    "grade ASC",
    "grade DESC",
}

# Friend list sort options (whitelist for SQL injection protection)
FRIEND_SORT_OPTIONS = {
    "name ASC",
    "name DESC",
    "created_at ASC",
    "created_at DESC",
    "belt_rank ASC",
    "belt_rank DESC",
    "friend_type ASC",
    "friend_type DESC",
}

# Session sort options (whitelist for SQL injection protection)
SESSION_SORT_OPTIONS = {
    "session_date ASC",
    "session_date DESC",
    "duration_minutes ASC",
    "duration_minutes DESC",
    "intensity ASC",
    "intensity DESC",
    "created_at ASC",
    "created_at DESC",
}

# ==============================================================================
# VISIBILITY LEVELS
# ==============================================================================

VISIBILITY_PRIVATE = "private"
VISIBILITY_FRIENDS = "friends"
VISIBILITY_PUBLIC = "public"

VISIBILITY_LEVELS = {
    VISIBILITY_PRIVATE,
    VISIBILITY_FRIENDS,
    VISIBILITY_PUBLIC,
}

# ==============================================================================
# CLASS TYPES
# ==============================================================================

# Sparring class types (require roll tracking)
CLASS_TYPE_GI = "gi"
CLASS_TYPE_NOGI = "no-gi"
CLASS_TYPE_OPEN_MAT = "open-mat"
CLASS_TYPE_COMPETITION = "competition"

SPARRING_CLASS_TYPES = {
    CLASS_TYPE_GI,
    CLASS_TYPE_NOGI,
    CLASS_TYPE_OPEN_MAT,
    CLASS_TYPE_COMPETITION,
}

# Non-sparring class types
CLASS_TYPE_SC = "s&c"
CLASS_TYPE_CARDIO = "cardio"
CLASS_TYPE_MOBILITY = "mobility"

NON_SPARRING_CLASS_TYPES = {
    CLASS_TYPE_SC,
    CLASS_TYPE_CARDIO,
    CLASS_TYPE_MOBILITY,
}

ALL_CLASS_TYPES = SPARRING_CLASS_TYPES | NON_SPARRING_CLASS_TYPES

# ==============================================================================
# REST DAY TYPES
# ==============================================================================

REST_TYPE_ACTIVE = "active"
REST_TYPE_FULL = "full"
REST_TYPE_INJURY = "injury"
REST_TYPE_SICK = "sick"
REST_TYPE_TRAVEL = "travel"
REST_TYPE_LIFE = "life"

REST_TYPES = {
    REST_TYPE_ACTIVE: "Active Recovery",
    REST_TYPE_FULL: "Full Rest",
    REST_TYPE_INJURY: "Injury / Rehab",
    REST_TYPE_SICK: "Sick Day",
    REST_TYPE_TRAVEL: "Travelling",
    REST_TYPE_LIFE: "Life Got in the Way",
}

# ==============================================================================
# TOMORROW INTENTIONS
# ==============================================================================

TOMORROW_INTENTIONS = {
    "train_gi": "🥋 Gi training",
    "train_nogi": "🩳 No-Gi training",
    "train_wrestling": "🤼 Wrestling",
    "train_open": "🔓 Open mat",
    "train_sc": "🏋️ S&C / Conditioning",
    "train_mobility": "🧘 Mobility / Yoga",
    "rest": "😴 Rest day",
    "unsure": "🤷 Not sure yet",
}

# ==============================================================================
# ACTIVITY TYPES
# ==============================================================================

ACTIVITY_TYPE_SESSION = "session"
ACTIVITY_TYPE_READINESS = "readiness"
ACTIVITY_TYPE_REST = "rest"

ACTIVITY_TYPES = {
    ACTIVITY_TYPE_SESSION,
    ACTIVITY_TYPE_READINESS,
    ACTIVITY_TYPE_REST,
}

# ==============================================================================
# BELT/GRADE LEVELS
# ==============================================================================

BELT_WHITE = "white"
BELT_BLUE = "blue"
BELT_PURPLE = "purple"
BELT_BROWN = "brown"
BELT_BLACK = "black"

BELT_LEVELS = {
    BELT_WHITE,
    BELT_BLUE,
    BELT_PURPLE,
    BELT_BROWN,
    BELT_BLACK,
}

# ==============================================================================
# API RATE LIMITS
# ==============================================================================

# Rate limit: requests per minute
RATE_LIMIT_PER_MINUTE = 60

# Rate limit: requests per hour
RATE_LIMIT_PER_HOUR = 1000

# ==============================================================================
# FILE UPLOAD LIMITS
# ==============================================================================

# Maximum file size for uploads (bytes)
MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# Maximum photos per activity
MAX_PHOTOS_PER_ACTIVITY = 3

# Allowed image extensions
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

# ==============================================================================
# CACHE TTL (Time To Live)
# ==============================================================================

# Cache durations in seconds
CACHE_TTL_1_MINUTE = 60
CACHE_TTL_5_MINUTES = 300
CACHE_TTL_15_MINUTES = 900
CACHE_TTL_1_HOUR = 3600
CACHE_TTL_1_DAY = 86400

# ==============================================================================
# VALIDATION LIMITS
# ==============================================================================

# Password minimum length
MIN_PASSWORD_LENGTH = 8

# Session duration limits (minutes)
MIN_SESSION_DURATION = 1
MAX_SESSION_DURATION = 480  # 8 hours

# Intensity scale
MIN_INTENSITY = 1
MAX_INTENSITY = 5

# Roll count limits
MIN_ROLL_COUNT = 0
MAX_ROLL_COUNT = 50

# ==============================================================================
# STREAK SETTINGS
# ==============================================================================

STREAK_TYPE_TRAINING = "training"
STREAK_TYPE_READINESS = "readiness"
STREAK_TYPE_CHECKIN = "checkin"

STREAK_TYPES = {
    STREAK_TYPE_TRAINING,
    STREAK_TYPE_READINESS,
    STREAK_TYPE_CHECKIN,
}

# Grace period for streaks (days)
STREAK_GRACE_DAYS = 1

# ==============================================================================
# MILESTONE THRESHOLDS
# ==============================================================================

MILESTONE_HOURS = [10, 25, 50, 100, 250, 500, 1000]
MILESTONE_SESSIONS = [10, 25, 50, 100, 250, 500]
MILESTONE_STREAK = [7, 14, 30, 60, 90, 180, 365]
MILESTONE_ROLLS = [50, 100, 250, 500, 1000]
MILESTONE_PARTNERS = [10, 25, 50, 100]
MILESTONE_TECHNIQUES = [10, 25, 50, 100]

MILESTONES = {
    "hours": MILESTONE_HOURS,
    "sessions": MILESTONE_SESSIONS,
    "streak": MILESTONE_STREAK,
    "rolls": MILESTONE_ROLLS,
    "partners": MILESTONE_PARTNERS,
    "techniques": MILESTONE_TECHNIQUES,
}

MILESTONE_LABELS = {
    "hours": "{} Hours on the Mat",
    "sessions": "{} Sessions Logged",
    "streak": "{}-Day Streak",
    "rolls": "{} Rolls Completed",
    "partners": "{} Training Partners",
    "techniques": "{} Techniques Practiced",
}

MILESTONE_QUOTES = [
    (
        "The more you sweat in training, the less you bleed in combat.",
        "Richard Marcinko",
    ),
    ("A black belt is a white belt who never quit.", "Unknown"),
    ("The ground is my ocean, I'm the shark.", "Jean Jacques Machado"),
    ("There is no losing, only winning or learning.", "Carlos Gracie Jr"),
    ("Be water, my friend.", "Bruce Lee"),
    ("Discipline equals freedom.", "Jocko Willink"),
    ("Train hard, fight easy.", "Alexander Suvorov"),
    ("The more you know, the less you need.", "Rickson Gracie"),
    ("Position before submission.", "Saulo Ribeiro"),
    ("Leave your ego at the door.", "Helio Gracie"),
]

# ==============================================================================
# DEFAULT VALUES
# ==============================================================================

DEFAULT_SESSION_DURATION = 60  # minutes
DEFAULT_DURATION = 60  # minutes (alias for backwards compatibility)
DEFAULT_INTENSITY = 4
DEFAULT_ROLL_COUNT = 0
DEFAULT_VISIBILITY = VISIBILITY_FRIENDS
DEFAULT_PAGE_SIZE = 20
DEFAULT_MAX_RESULTS = 100


# ==============================================================================
# COMMON PASSWORDS (for password strength validation)
# ==============================================================================

# Top ~100 most common passwords (lowercase for case-insensitive comparison).
# Used to reject easily guessed passwords during registration and password reset.
COMMON_PASSWORDS = {
    "password",
    "123456",
    "12345678",
    "1234567890",
    "1234567",
    "123456789",
    "12345",
    "1234",
    "qwerty",
    "abc123",
    "monkey",
    "letmein",
    "trustno1",
    "dragon",
    "baseball",
    "iloveyou",
    "master",
    "sunshine",
    "ashley",
    "michael",
    "shadow",
    "123123",
    "654321",
    "superman",
    "qazwsx",
    "michael1",
    "football",
    "password1",
    "password123",
    "welcome",
    "welcome1",
    "p@ssw0rd",
    "admin",
    "login",
    "princess",
    "starwars",
    "solo",
    "passw0rd",
    "hello",
    "charlie",
    "donald",
    "password2",
    "qwerty123",
    "letmein1",
    "trustno2",
    "whatever",
    "freedom",
    "batman",
    "access",
    "master1",
    "diamond",
    "hello123",
    "soccer",
    "thomas",
    "ranger",
    "buster",
    "tigger",
    "robert",
    "soccer1",
    "batman1",
    "test",
    "pass",
    "killer",
    "hockey",
    "george",
    "charlie1",
    "andrew",
    "michelle",
    "love",
    "jordan",
    "jessica",
    "pepper",
    "daniel",
    "hunter",
    "joshua",
    "maggie",
    "ginger",
    "matthew",
    "amanda",
    "summer",
    "nicole",
    "abcdef",
    "hannah",
    "orange",
    "merlin",
    "cookie",
    "taylor",
    "jackson",
    "oliver",
    "jennifer",
    "computer",
    "midnight",
    "samantha",
    "corvette",
    "mustang",
    "matrix",
    "sparky",
    "camaro",
}
