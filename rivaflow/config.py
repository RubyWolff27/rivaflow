"""Application configuration."""
from pathlib import Path

# Data stored in user's home directory (survives pip upgrades)
APP_DIR = Path.home() / ".rivaflow"
DB_PATH = APP_DIR / "rivaflow.db"

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
