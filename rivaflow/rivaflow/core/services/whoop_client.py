"""HTTP client for the WHOOP Developer API."""

import logging
from urllib.parse import urlencode

import httpx

from rivaflow.core.exceptions import ExternalServiceError
from rivaflow.core.settings import settings

logger = logging.getLogger(__name__)

WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v2"
WHOOP_SCOPES = "read:workout read:recovery read:sleep read:cycles read:body_measurement read:profile offline"

TIMEOUT = 15.0


class WhoopClient:
    """Synchronous HTTP client for the WHOOP API."""

    def get_authorization_url(self, state: str) -> str:
        """Build the OAuth authorization URL."""
        params = {
            "response_type": "code",
            "client_id": settings.WHOOP_CLIENT_ID,
            "redirect_uri": settings.WHOOP_REDIRECT_URI,
            "scope": WHOOP_SCOPES,
            "state": state,
        }
        return f"{WHOOP_AUTH_URL}?{urlencode(params)}"

    def exchange_code(self, code: str) -> dict:
        """Exchange an authorization code for access + refresh tokens."""
        try:
            response = httpx.post(
                WHOOP_TOKEN_URL,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "client_id": settings.WHOOP_CLIENT_ID,
                    "client_secret": settings.WHOOP_CLIENT_SECRET,
                    "redirect_uri": settings.WHOOP_REDIRECT_URI,
                },
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("WHOOP token exchange failed: %s", e.response.text)
            raise ExternalServiceError(
                "Failed to exchange WHOOP authorization code"
            ) from e
        except httpx.TimeoutException as e:
            raise ExternalServiceError("WHOOP API timed out") from e

    def refresh_tokens(self, refresh_token: str) -> dict:
        """Refresh an expired access token."""
        try:
            response = httpx.post(
                WHOOP_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": settings.WHOOP_CLIENT_ID,
                    "client_secret": settings.WHOOP_CLIENT_SECRET,
                },
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("WHOOP token refresh failed: %s", e.response.text)
            raise ExternalServiceError("Failed to refresh WHOOP tokens") from e
        except httpx.TimeoutException as e:
            raise ExternalServiceError("WHOOP API timed out") from e

    def get_profile(self, access_token: str) -> dict:
        """Get the WHOOP user profile."""
        return self._get(f"{WHOOP_API_BASE}/user/profile/basic", access_token)

    def get_workouts(
        self,
        access_token: str,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict:
        """Get workouts with optional time range and pagination."""
        params: dict = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if next_token:
            params["nextToken"] = next_token
        return self._get(
            f"{WHOOP_API_BASE}/activity/workout",
            access_token,
            params=params,
        )

    def get_recovery(
        self,
        access_token: str,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict:
        """Get recovery data with optional time range and pagination."""
        params: dict = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if next_token:
            params["nextToken"] = next_token
        return self._get(
            f"{WHOOP_API_BASE}/recovery",
            access_token,
            params=params,
        )

    def get_sleep(
        self,
        access_token: str,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict:
        """Get sleep data with optional time range and pagination."""
        params: dict = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if next_token:
            params["nextToken"] = next_token
        return self._get(
            f"{WHOOP_API_BASE}/activity/sleep",
            access_token,
            params=params,
        )

    def get_cycles(
        self,
        access_token: str,
        start: str | None = None,
        end: str | None = None,
        next_token: str | None = None,
    ) -> dict:
        """Get physiological cycles with optional time range and pagination."""
        params: dict = {}
        if start:
            params["start"] = start
        if end:
            params["end"] = end
        if next_token:
            params["nextToken"] = next_token
        return self._get(
            f"{WHOOP_API_BASE}/cycle",
            access_token,
            params=params,
        )

    def get_workout_by_id(self, access_token: str, workout_id: str) -> dict:
        """Get a single workout by its WHOOP ID."""
        return self._get(
            f"{WHOOP_API_BASE}/activity/workout/{workout_id}",
            access_token,
        )

    def get_body_measurement(self, access_token: str) -> dict:
        """Get the latest body measurement."""
        return self._get(
            f"{WHOOP_API_BASE}/body_measurement",
            access_token,
        )

    def revoke_access(self, access_token: str) -> bool:
        """Best-effort token revocation."""
        try:
            response = httpx.post(
                f"{WHOOP_API_BASE}/oauth/token/revoke",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=TIMEOUT,
            )
            return response.status_code < 400
        except Exception:
            logger.warning("WHOOP token revocation failed (best-effort)")
            return False

    def _get(self, url: str, access_token: str, params: dict | None = None) -> dict:
        """Make an authenticated GET request to the WHOOP API."""
        try:
            response = httpx.get(
                url,
                headers={"Authorization": f"Bearer {access_token}"},
                params=params,
                timeout=TIMEOUT,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            logger.error("WHOOP API error: %s", e.response.status_code)
            raise ExternalServiceError(
                f"WHOOP API request failed ({e.response.status_code})"
            ) from e
        except httpx.TimeoutException as e:
            raise ExternalServiceError("WHOOP API timed out") from e
