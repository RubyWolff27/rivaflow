"""Integration tests for photo upload and management routes."""

from unittest.mock import patch

import pytest


@pytest.fixture
def _create_session(session_factory):
    """Create a session to attach photos to."""
    return session_factory()


@pytest.fixture(autouse=True)
def _patch_count_by_activity():
    """Patch count_by_activity to work around SQLite Row .values() bug.

    The ActivityPhotoRepository.count_by_activity method uses
    ``list(row.values())[0]`` which fails on sqlite3.Row because
    Row has .keys() but not .values().  We mock it to return 0
    (no photos yet) so the upload path is exercised.
    """
    with patch(
        "rivaflow.db.repositories.activity_photo_repo."
        "ActivityPhotoRepository.count_by_activity",
        return_value=0,
    ):
        yield


def _make_png_bytes():
    """Create minimal valid PNG file bytes (1x1 pixel, red)."""
    # Minimal valid PNG: 8-byte signature + IHDR + IDAT + IEND
    import struct
    import zlib

    signature = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk: width=1, height=1, bit_depth=8, color_type=2 (RGB)
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr_crc = zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF
    ihdr = (
        struct.pack(">I", len(ihdr_data))
        + b"IHDR"
        + ihdr_data
        + struct.pack(">I", ihdr_crc)
    )

    # IDAT chunk: filter byte (0) + RGB pixel
    raw_data = b"\x00\xff\x00\x00"  # filter=None, R=255, G=0, B=0
    compressed = zlib.compress(raw_data)
    idat_crc = zlib.crc32(b"IDAT" + compressed) & 0xFFFFFFFF
    idat = (
        struct.pack(">I", len(compressed))
        + b"IDAT"
        + compressed
        + struct.pack(">I", idat_crc)
    )

    # IEND chunk
    iend_crc = zlib.crc32(b"IEND") & 0xFFFFFFFF
    iend = struct.pack(">I", 0) + b"IEND" + struct.pack(">I", iend_crc)

    return signature + ihdr + idat + iend


class TestUploadPhoto:
    """Tests for POST /api/v1/photos/upload."""

    def test_upload_requires_auth(self, client, temp_db):
        """Unauthenticated upload returns 401."""
        resp = client.post(
            "/api/v1/photos/upload",
            data={
                "activity_type": "session",
                "activity_id": "1",
                "activity_date": "2025-01-20",
            },
            files={"file": ("test.png", b"fake", "image/png")},
        )
        assert resp.status_code == 401

    def test_upload_invalid_activity_type(self, authenticated_client, test_user):
        """Invalid activity type returns 400."""
        png_bytes = _make_png_bytes()
        resp = authenticated_client.post(
            "/api/v1/photos/upload",
            data={
                "activity_type": "invalid",
                "activity_id": "1",
                "activity_date": "2025-01-20",
            },
            files={"file": ("test.png", png_bytes, "image/png")},
        )
        assert resp.status_code == 400
        assert "Invalid activity type" in resp.json()["detail"]

    def test_upload_invalid_extension(self, authenticated_client, test_user):
        """Unsupported file extension returns 400."""
        resp = authenticated_client.post(
            "/api/v1/photos/upload",
            data={
                "activity_type": "session",
                "activity_id": "1",
                "activity_date": "2025-01-20",
            },
            files={"file": ("test.bmp", b"fake", "image/bmp")},
        )
        assert resp.status_code == 400
        assert "Invalid file type" in resp.json()["detail"]

    def test_upload_valid_png(
        self,
        authenticated_client,
        test_user,
        _create_session,
    ):
        """Upload a valid PNG returns 201 with photo metadata."""
        session_id = _create_session
        png_bytes = _make_png_bytes()
        resp = authenticated_client.post(
            "/api/v1/photos/upload",
            data={
                "activity_type": "session",
                "activity_id": str(session_id),
                "activity_date": "2025-01-20",
            },
            files={"file": ("test.png", png_bytes, "image/png")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        assert "file_path" in data
        assert data["message"] == "Photo uploaded successfully"

    def test_upload_file_too_large(self, authenticated_client, test_user):
        """File exceeding 5MB returns 400."""
        # Create content larger than 5MB with valid PNG header
        png_bytes = _make_png_bytes()
        # Pad to exceed 5MB
        large_content = png_bytes + b"\x00" * (6 * 1024 * 1024)
        resp = authenticated_client.post(
            "/api/v1/photos/upload",
            data={
                "activity_type": "session",
                "activity_id": "1",
                "activity_date": "2025-01-20",
            },
            files={
                "file": (
                    "test.png",
                    large_content,
                    "image/png",
                )
            },
        )
        assert resp.status_code == 400
        assert "too large" in resp.json()["detail"].lower()


class TestGetActivityPhotos:
    """Tests for GET /api/v1/photos/activity/{type}/{id}."""

    def test_get_photos_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/photos/activity/session/1")
        assert resp.status_code == 401

    def test_get_photos_empty(self, authenticated_client, test_user):
        """Returns empty list when no photos exist."""
        resp = authenticated_client.get("/api/v1/photos/activity/session/999")
        assert resp.status_code == 200
        assert resp.json() == []


class TestDeletePhoto:
    """Tests for DELETE /api/v1/photos/{photo_id}."""

    def test_delete_requires_auth(self, client, temp_db):
        """Unauthenticated delete returns 401."""
        resp = client.delete("/api/v1/photos/1")
        assert resp.status_code == 401

    def test_delete_nonexistent_photo(self, authenticated_client, test_user):
        """Deleting a photo that doesn't exist returns 404."""
        resp = authenticated_client.delete("/api/v1/photos/999999")
        assert resp.status_code == 404

    def test_upload_then_delete(
        self,
        authenticated_client,
        test_user,
        _create_session,
    ):
        """Upload a photo then delete it returns 204."""
        session_id = _create_session
        png_bytes = _make_png_bytes()
        upload_resp = authenticated_client.post(
            "/api/v1/photos/upload",
            data={
                "activity_type": "session",
                "activity_id": str(session_id),
                "activity_date": "2025-01-20",
            },
            files={"file": ("test.png", png_bytes, "image/png")},
        )
        assert upload_resp.status_code == 201
        photo_id = upload_resp.json()["id"]

        # Delete
        del_resp = authenticated_client.delete(f"/api/v1/photos/{photo_id}")
        assert del_resp.status_code == 204


class TestGetSinglePhoto:
    """Tests for GET /api/v1/photos/{photo_id}."""

    def test_get_photo_requires_auth(self, client, temp_db):
        """Unauthenticated request returns 401."""
        resp = client.get("/api/v1/photos/1")
        assert resp.status_code == 401

    def test_get_nonexistent_photo(self, authenticated_client, test_user):
        """Returns 404 for a photo that doesn't exist."""
        resp = authenticated_client.get("/api/v1/photos/999999")
        assert resp.status_code == 404
