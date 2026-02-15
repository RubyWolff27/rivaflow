"""Application configuration.

DEPRECATED: This module is maintained for backwards compatibility.
New code should import from rivaflow.core.settings instead.
"""

from rivaflow.core.settings import settings

# Legacy imports - use settings module instead
APP_DIR = settings.APP_DIR
DB_PATH = settings.DB_PATH
DATABASE_URL = settings.DATABASE_URL
DB_TYPE = settings.DB_TYPE


# Backwards compatibility function
def get_db_type():
    """
    Dynamically determine database type.

    DEPRECATED: Use settings.DB_TYPE instead.
    """
    return settings.DB_TYPE


# Defaults
DEFAULT_DURATION = 60
DEFAULT_INTENSITY = 4
DEFAULT_ROLLS = 0

# Class types that require rolls input
SPARRING_CLASS_TYPES = {"gi", "no-gi", "open-mat", "competition"}
NON_SPARRING_CLASS_TYPES = {
    "s&c",
    "cardio",
    "mobility",
}
ALL_CLASS_TYPES = SPARRING_CLASS_TYPES | NON_SPARRING_CLASS_TYPES

# Visibility levels
VISIBILITY_LEVELS = {"private", "attendance", "summary", "full"}

# ==============================================================================
# ENGAGEMENT FEATURES (v0.2)
# ==============================================================================

# Rest day types
REST_TYPES = {
    "active": "Active Recovery",
    "full": "Full Rest",
    "injury": "Injury / Rehab",
    "sick": "Sick Day",
    "travel": "Travelling",
    "life": "Life Got in the Way",
}

# Tomorrow intentions
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

# Streak settings
STREAK_GRACE_DAYS = 1  # Miss 1 day without breaking streak

# Milestone thresholds
MILESTONES = {
    "hours": [10, 25, 50, 100, 250, 500, 1000],
    "sessions": [10, 25, 50, 100, 250, 500],
    "streak": [7, 14, 30, 60, 90, 180, 365],
    "rolls": [50, 100, 250, 500, 1000],
    "partners": [10, 25, 50, 100],
    "techniques": [10, 25, 50, 100],
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
