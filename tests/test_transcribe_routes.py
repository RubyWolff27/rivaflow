"""Integration tests for audio transcription routes."""

from io import BytesIO
from unittest.mock import patch


class TestTranscribeAudio:
    """Tests for POST /api/v1/transcribe/."""

    def test_transcribe_requires_auth(self, client, temp_db):
        """Test that transcription requires authentication."""
        response = client.post(
            "/api/v1/transcribe/",
            files={"file": ("audio.webm", b"fake-audio", "audio/webm")},
        )
        assert response.status_code == 401

    def test_transcribe_no_api_key(self, authenticated_client, test_user):
        """Test transcription returns 503 when OpenAI key not configured."""
        with patch("rivaflow.api.routes.transcribe.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            response = authenticated_client.post(
                "/api/v1/transcribe/",
                files={"file": ("audio.webm", b"fake-audio", "audio/webm")},
            )
            assert response.status_code == 503
            data = response.json()
            assert "not configured" in data["detail"]

    def test_transcribe_unsupported_format(self, authenticated_client, test_user):
        """Test transcription rejects unsupported audio formats."""
        with patch("rivaflow.api.routes.transcribe.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            response = authenticated_client.post(
                "/api/v1/transcribe/",
                files={
                    "file": (
                        "file.txt",
                        b"not-audio",
                        "text/plain",
                    )
                },
            )
            assert response.status_code == 400
            data = response.json()
            assert "Unsupported" in data["detail"]

    def test_transcribe_empty_file(self, authenticated_client, test_user):
        """Test transcription rejects empty audio files."""
        with patch("rivaflow.api.routes.transcribe.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            response = authenticated_client.post(
                "/api/v1/transcribe/",
                files={"file": ("audio.webm", b"", "audio/webm")},
            )
            assert response.status_code == 400
            data = response.json()
            assert "Empty" in data["detail"]

    def test_transcribe_file_too_large(self, authenticated_client, test_user):
        """Test transcription rejects files over 25MB.

        The RequestSizeLimitMiddleware may return 413 before the route
        handler gets a chance to check the size, so we accept both 400
        and 413 as valid rejection codes.
        """
        with patch("rivaflow.api.routes.transcribe.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            # Create a file just over the limit
            large_data = b"x" * (26 * 1024 * 1024)
            response = authenticated_client.post(
                "/api/v1/transcribe/",
                files={"file": ("audio.webm", BytesIO(large_data), "audio/webm")},
            )
            assert response.status_code in (400, 413)

    def test_transcribe_accepted_mime_types(self, authenticated_client, test_user):
        """Test that all documented MIME types are accepted (past format check)."""
        accepted_types = [
            "audio/webm",
            "audio/mp4",
            "audio/mpeg",
            "audio/mp3",
            "audio/wav",
            "audio/ogg",
            "audio/x-m4a",
            "video/webm",
        ]
        with patch("rivaflow.api.routes.transcribe.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = "test-key"
            for mime in accepted_types:
                response = authenticated_client.post(
                    "/api/v1/transcribe/",
                    files={"file": ("audio.test", b"fake-audio-data", mime)},
                )
                # Should pass format check (will fail at API call, not 400)
                assert response.status_code != 400 or (
                    "Unsupported" not in response.json().get("detail", "")
                ), f"MIME type {mime} should be accepted"
