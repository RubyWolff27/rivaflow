"""CLI user context management.

KNOWN LIMITATION - Documented in README.md:
The CLI currently supports single-user mode only (defaults to user_id=1).
For multi-user accounts, users should use the Web App interface.
Multi-user CLI authentication is planned for v0.2.

In a true multi-user CLI (like Strava), users would:
1. Login with email/password or API token
2. Store session in ~/.rivaflow/session
3. All commands would use authenticated user's ID

Current behavior: Defaults to user_id=1 for local/single-user installations.
Can be overridden with RIVAFLOW_USER_ID environment variable for testing.
"""
import os
from typing import Optional


def get_current_user_id() -> int:
    """Get the current CLI user ID.

    TODO: Replace with actual authentication.
    Currently returns user_id=1 for backwards compatibility.

    Future implementation should:
    - Check for session file (~/.rivaflow/session)
    - Validate session token
    - Return authenticated user's ID
    - Prompt for login if no session found

    Returns:
        int: User ID for current CLI session
    """
    # TODO: Implement actual authentication
    # For now, default to user_id=1
    # Check environment variable for override (useful for testing)
    return int(os.environ.get("RIVAFLOW_USER_ID", "1"))


def require_auth() -> int:
    """Require CLI authentication and return user ID.

    TODO: Implement proper authentication flow.

    Returns:
        int: Authenticated user ID

    Raises:
        SystemExit: If user is not authenticated
    """
    # TODO: Check if user is authenticated
    # If not, prompt for login or show error
    return get_current_user_id()
