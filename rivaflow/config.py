"""Application configuration."""
import os
from pathlib import Path

# Data stored in user's home directory (survives pip upgrades)
APP_DIR = Path.home() / ".rivaflow"
DB_PATH = APP_DIR / "rivaflow.db"

# Database configuration
# If DATABASE_URL is set (production), use it. Otherwise, use local SQLite.
DATABASE_URL = os.getenv("DATABASE_URL")
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    # Render uses postgres:// but psycopg2 expects postgresql://
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Determine database type
DB_TYPE = "postgresql" if DATABASE_URL else "sqlite"

# Defaults
DEFAULT_DURATION = 60
DEFAULT_INTENSITY = 4
DEFAULT_ROLLS = 0

# Class types that require rolls input
SPARRING_CLASS_TYPES = {"gi", "no-gi", "wrestling", "judo", "open-mat"}
NON_SPARRING_CLASS_TYPES = {"s&c", "mobility", "yoga", "rehab", "physio", "drilling"}
ALL_CLASS_TYPES = SPARRING_CLASS_TYPES | NON_SPARRING_CLASS_TYPES

# Visibility levels
VISIBILITY_LEVELS = {"private", "attendance", "summary", "full"}

# ==============================================================================
# ENGAGEMENT FEATURES (v0.2)
# ==============================================================================

# Rest day types
REST_TYPES = {
    "recovery": "Active recovery",
    "life": "Life got in the way",
    "injury": "Injury/rehab",
    "travel": "Traveling"
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
    "unsure": "🤷 Not sure yet"
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
    "techniques": [10, 25, 50, 100]
}

MILESTONE_LABELS = {
    "hours": "{} Hours on the Mat",
    "sessions": "{} Sessions Logged",
    "streak": "{}-Day Streak",
    "rolls": "{} Rolls Completed",
    "partners": "{} Training Partners",
    "techniques": "{} Techniques Practiced"
}

MILESTONE_QUOTES = [
    ("The more you sweat in training, the less you bleed in combat.", "Richard Marcinko"),
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
