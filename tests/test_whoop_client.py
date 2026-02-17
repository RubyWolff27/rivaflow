"""Tests for WhoopClient — WHOOP Developer API HTTP client (mocked)."""

from unittest.mock import MagicMock, patch

import httpx
import pytest

from rivaflow.core.exceptions import ExternalServiceError
from rivaflow.core.services.whoop_client import (
    WHOOP_AUTH_URL,
    WhoopClient,
)


@pytest.fixture
def client():
    return WhoopClient()


# ---------------------------------------------------------------------------
# get_authorization_url
# ---------------------------------------------------------------------------


class TestGetAuthorizationUrl:
    def test_contains_auth_url(self, client):
        url = client.get_authorization_url(state="abc123")
        assert url.startswith(WHOOP_AUTH_URL)

    def test_includes_state(self, client):
        url = client.get_authorization_url(state="mystate")
        assert "state=mystate" in url

    def test_includes_scopes(self, client):
        url = client.get_authorization_url(state="s")
        # scopes are URL-encoded (space -> +)
        assert "scope=" in url

    def test_includes_response_type_code(self, client):
        url = client.get_authorization_url(state="s")
        assert "response_type=code" in url


# ---------------------------------------------------------------------------
# exchange_code
# ---------------------------------------------------------------------------


class TestExchangeCode:
    def test_success(self, client):
        token_response = {
            "access_token": "acc_tok",
            "refresh_token": "ref_tok",
            "expires_in": 3600,
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = token_response
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.post", return_value=mock_resp
        ) as mock_post:
            result = client.exchange_code("auth_code_123")

        assert result == token_response
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["data"]["code"] == "auth_code_123"
        assert call_kwargs.kwargs["data"]["grant_type"] == "authorization_code"

    def test_http_error_raises_external_service_error(self, client):
        mock_resp = MagicMock()
        mock_resp.text = "bad request"
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "400", request=MagicMock(), response=mock_resp
        )
        # Attach response to the exception
        mock_resp.status_code = 400

        with patch(
            "rivaflow.core.services.whoop_client.httpx.post", return_value=mock_resp
        ):
            with pytest.raises(ExternalServiceError, match="exchange"):
                client.exchange_code("bad_code")

    def test_timeout_raises_external_service_error(self, client):
        with patch(
            "rivaflow.core.services.whoop_client.httpx.post",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(ExternalServiceError, match="timed out"):
                client.exchange_code("code")


# ---------------------------------------------------------------------------
# refresh_tokens
# ---------------------------------------------------------------------------


class TestRefreshTokens:
    def test_success(self, client):
        token_response = {
            "access_token": "new_acc",
            "refresh_token": "new_ref",
            "expires_in": 3600,
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = token_response
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.post", return_value=mock_resp
        ) as mock_post:
            result = client.refresh_tokens("old_refresh_token")

        assert result == token_response
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["data"]["grant_type"] == "refresh_token"
        assert call_kwargs.kwargs["data"]["refresh_token"] == "old_refresh_token"

    def test_http_error(self, client):
        mock_resp = MagicMock()
        mock_resp.text = "invalid grant"
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=mock_resp
        )

        with patch(
            "rivaflow.core.services.whoop_client.httpx.post", return_value=mock_resp
        ):
            with pytest.raises(ExternalServiceError, match="refresh"):
                client.refresh_tokens("bad_token")

    def test_timeout(self, client):
        with patch(
            "rivaflow.core.services.whoop_client.httpx.post",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(ExternalServiceError, match="timed out"):
                client.refresh_tokens("tok")


# ---------------------------------------------------------------------------
# get_workouts — WHOOP API zone keys and energy field gotchas
# ---------------------------------------------------------------------------


class TestGetWorkouts:
    def _bjj_workout(self):
        """Return a WHOOP workout payload with BJJ sport_id=76 and correct field names."""
        return {
            "records": [
                {
                    "id": 12345,
                    "sport_id": 76,  # BJJ
                    "score": {
                        "strain": 14.2,
                        "kilojoule": 1850.5,  # singular, NOT kilojoules
                        "average_heart_rate": 145,
                        "max_heart_rate": 178,
                        "zone_duration": {
                            "zone_one_milli": 120000,  # _milli, NOT _ms
                            "zone_two_milli": 240000,
                            "zone_three_milli": 300000,
                            "zone_four_milli": 180000,
                            "zone_five_milli": 60000,
                        },
                    },
                    "start": "2026-02-15T10:00:00Z",
                    "end": "2026-02-15T11:00:00Z",
                }
            ],
            "next_token": None,
        }

    def test_fetches_workouts(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._bjj_workout()
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ):
            result = client.get_workouts("access_tok")

        assert len(result["records"]) == 1
        workout = result["records"][0]
        assert workout["sport_id"] == 76

    def test_zone_keys_use_milli_suffix(self, client):
        """WHOOP zone keys are zone_one_milli, NOT zone_one_ms."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._bjj_workout()
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ):
            result = client.get_workouts("tok")

        zones = result["records"][0]["score"]["zone_duration"]
        assert "zone_one_milli" in zones
        assert "zone_two_milli" in zones
        # Verify the wrong key is NOT present
        assert "zone_one_ms" not in zones

    def test_energy_field_is_singular_kilojoule(self, client):
        """WHOOP energy field is 'kilojoule' (singular), NOT 'kilojoules'."""
        mock_resp = MagicMock()
        mock_resp.json.return_value = self._bjj_workout()
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ):
            result = client.get_workouts("tok")

        score = result["records"][0]["score"]
        assert "kilojoule" in score
        assert "kilojoules" not in score

    def test_passes_start_end_params(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"records": [], "next_token": None}
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ) as mock_get:
            client.get_workouts("tok", start="2026-01-01", end="2026-02-01")

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["start"] == "2026-01-01"
        assert call_kwargs.kwargs["params"]["end"] == "2026-02-01"

    def test_passes_next_token(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"records": [], "next_token": None}
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ) as mock_get:
            client.get_workouts("tok", next_token="page2")

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["nextToken"] == "page2"

    def test_http_error(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=mock_resp
        )

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ):
            with pytest.raises(ExternalServiceError):
                client.get_workouts("tok")

    def test_timeout(self, client):
        with patch(
            "rivaflow.core.services.whoop_client.httpx.get",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(ExternalServiceError, match="timed out"):
                client.get_workouts("tok")


# ---------------------------------------------------------------------------
# get_recovery
# ---------------------------------------------------------------------------


class TestGetRecovery:
    def test_fetches_recovery(self, client):
        recovery_data = {
            "records": [
                {
                    "cycle_id": 1,
                    "score": {
                        "recovery_score": 78.0,
                        "resting_heart_rate": 52.0,
                        "hrv_rmssd_milli": 45.3,
                        "spo2_percentage": 97.0,
                        "skin_temp_celsius": 33.8,
                    },
                }
            ],
            "next_token": None,
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = recovery_data
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ):
            result = client.get_recovery("tok")

        assert len(result["records"]) == 1
        assert result["records"][0]["score"]["recovery_score"] == 78.0

    def test_passes_date_range(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"records": [], "next_token": None}
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ) as mock_get:
            client.get_recovery("tok", start="2026-01-01", end="2026-02-01")

        call_kwargs = mock_get.call_args
        assert call_kwargs.kwargs["params"]["start"] == "2026-01-01"
        assert call_kwargs.kwargs["params"]["end"] == "2026-02-01"

    def test_timeout(self, client):
        with patch(
            "rivaflow.core.services.whoop_client.httpx.get",
            side_effect=httpx.TimeoutException("timeout"),
        ):
            with pytest.raises(ExternalServiceError, match="timed out"):
                client.get_recovery("tok")


# ---------------------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------------------


class TestGetProfile:
    def test_fetches_profile(self, client):
        profile_data = {
            "user_id": 99,
            "first_name": "Helio",
            "last_name": "Gracie",
            "email": "helio@bjj.com",
        }
        mock_resp = MagicMock()
        mock_resp.json.return_value = profile_data
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ) as mock_get:
            result = client.get_profile("tok")

        assert result["first_name"] == "Helio"
        call_url = mock_get.call_args.args[0]
        assert "/user/profile/basic" in call_url


# ---------------------------------------------------------------------------
# get_sleep / get_cycles / get_workout_by_id / get_body_measurement
# ---------------------------------------------------------------------------


class TestOtherEndpoints:
    def _mock_get(self, return_value):
        mock_resp = MagicMock()
        mock_resp.json.return_value = return_value
        mock_resp.raise_for_status = MagicMock()
        return mock_resp

    def test_get_sleep(self, client):
        data = {"records": [{"id": 1, "score": {"total_sleep_duration": 28800000}}]}
        with patch(
            "rivaflow.core.services.whoop_client.httpx.get",
            return_value=self._mock_get(data),
        ) as mock_get:
            result = client.get_sleep("tok", start="2026-01-01")
        assert result["records"][0]["id"] == 1
        assert "sleep" in mock_get.call_args.args[0]

    def test_get_cycles(self, client):
        data = {"records": [{"id": 42}], "next_token": None}
        with patch(
            "rivaflow.core.services.whoop_client.httpx.get",
            return_value=self._mock_get(data),
        ) as mock_get:
            result = client.get_cycles("tok")
        assert result["records"][0]["id"] == 42
        assert "cycle" in mock_get.call_args.args[0]

    def test_get_workout_by_id(self, client):
        data = {"id": 555, "sport_id": 76}
        with patch(
            "rivaflow.core.services.whoop_client.httpx.get",
            return_value=self._mock_get(data),
        ) as mock_get:
            result = client.get_workout_by_id("tok", "555")
        assert result["id"] == 555
        assert "555" in mock_get.call_args.args[0]

    def test_get_body_measurement(self, client):
        data = {"weight_kilogram": 80.0, "height_meter": 1.78}
        with patch(
            "rivaflow.core.services.whoop_client.httpx.get",
            return_value=self._mock_get(data),
        ):
            result = client.get_body_measurement("tok")
        assert result["weight_kilogram"] == 80.0


# ---------------------------------------------------------------------------
# revoke_access
# ---------------------------------------------------------------------------


class TestRevokeAccess:
    def test_success(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 200

        with patch(
            "rivaflow.core.services.whoop_client.httpx.post", return_value=mock_resp
        ):
            assert client.revoke_access("tok") is True

    def test_failure_returns_false(self, client):
        mock_resp = MagicMock()
        mock_resp.status_code = 401

        with patch(
            "rivaflow.core.services.whoop_client.httpx.post", return_value=mock_resp
        ):
            assert client.revoke_access("tok") is False

    def test_exception_returns_false(self, client):
        with patch(
            "rivaflow.core.services.whoop_client.httpx.post",
            side_effect=Exception("network"),
        ):
            assert client.revoke_access("tok") is False


# ---------------------------------------------------------------------------
# _get (internal) — auth header
# ---------------------------------------------------------------------------


class TestAuthHeader:
    def test_sends_bearer_token(self, client):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {}
        mock_resp.raise_for_status = MagicMock()

        with patch(
            "rivaflow.core.services.whoop_client.httpx.get", return_value=mock_resp
        ) as mock_get:
            client.get_profile("my_secret_token")

        call_kwargs = mock_get.call_args
        assert (
            call_kwargs.kwargs["headers"]["Authorization"] == "Bearer my_secret_token"
        )
