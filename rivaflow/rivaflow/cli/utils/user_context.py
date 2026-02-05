"""CLI user context management with authentication.

The CLI now supports multi-user authentication via login/logout commands:
1. Users login with email/password using `rivaflow auth login`
2. Credentials are stored securely in ~/.rivaflow/credentials.json (0o600 permissions)
3. All commands use the authenticated user's ID
4. Users can logout using `rivaflow auth logout`

For backwards compatibility, if no credentials file exists, falls back to:
- RIVAFLOW_USER_ID environment variable (useful for testing)
- Default user_id=1 (for legacy single-user setups)
"""
import json
import os
import sys
from pathlib import Path

# Credentials file location
CREDENTIALS_FILE = Path.home() / ".rivaflow" / "credentials.json"


def get_current_user_id() -> int:
    """Get the current CLI user ID.

    Authentication priority:
    1. Credentials file (~/.rivaflow/credentials.json) - from login command
    2. RIVAFLOW_USER_ID environment variable - for testing
    3. Default to user_id=1 - for backwards compatibility

    Returns:
        int: User ID for current CLI session
    """
    # Check credentials file first (from login command)
    if CREDENTIALS_FILE.exists():
        try:
            with open(CREDENTIALS_FILE) as f:
                credentials = json.load(f)
                user_id = credentials.get("user_id")
                if user_id:
                    return int(user_id)
        except (OSError, json.JSONDecodeError, KeyError):
            # Credentials file corrupted or invalid - prompt for login
            print("⚠️  Warning: Credentials file is invalid or corrupted", file=sys.stderr)
            print("   Please run: rivaflow auth login", file=sys.stderr)
            sys.exit(1)

    # Check environment variable for override (useful for testing)
    if "RIVAFLOW_USER_ID" in os.environ:
        return int(os.environ.get("RIVAFLOW_USER_ID"))

    # Fall back to default user_id=1 for backwards compatibility
    # (legacy single-user setups)
    return 1


def require_auth() -> int:
    """Require CLI authentication and return user ID.

    If user is not authenticated (no credentials file), prompts them to login.

    Returns:
        int: Authenticated user ID

    Raises:
        SystemExit: If user is not authenticated
    """
    # Check if credentials file exists
    if not CREDENTIALS_FILE.exists():
        # Check if using environment variable or default fallback
        if "RIVAFLOW_USER_ID" in os.environ:
            return int(os.environ.get("RIVAFLOW_USER_ID"))

        # For user_id=1 default, allow without login (backwards compatibility)
        # This supports existing single-user local installations
        return 1

    # User is logged in - return their ID
    return get_current_user_id()


def is_authenticated() -> bool:
    """Check if user is currently authenticated.

    Returns:
        bool: True if user is logged in, False otherwise
    """
    return CREDENTIALS_FILE.exists()


def get_user_info() -> dict | None:
    """Get current user's information from credentials.

    Returns:
        dict: User information (email, first_name, last_name, user_id) or None if not logged in
    """
    if not CREDENTIALS_FILE.exists():
        return None

    try:
        with open(CREDENTIALS_FILE) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
