"""Tests for storage_service — local and S3 file storage backends."""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import rivaflow.core.services.storage_service as storage_mod

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _reset_singleton():
    """Reset the module-level storage singleton between tests."""
    storage_mod._storage = None
    yield
    storage_mod._storage = None


@pytest.fixture()
def local_backend(monkeypatch):
    """Create a _LocalBackend using a temporary uploads directory."""
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    tmp = Path(tempfile.mkdtemp())
    # Patch the base path used by _LocalBackend.__init__
    backend = storage_mod._LocalBackend()
    backend._base = tmp
    yield backend
    shutil.rmtree(tmp, ignore_errors=True)


# ---------------------------------------------------------------------------
# _LocalBackend tests
# ---------------------------------------------------------------------------


class TestLocalBackend:
    """Tests for the local filesystem backend."""

    def test_is_local(self, local_backend):
        """Local backend reports is_local=True."""
        assert local_backend.is_local is True

    def test_upload_creates_file(self, local_backend):
        """Uploading content creates a file on disk."""
        url = local_backend.upload("avatars", "test.jpg", b"\xff\xd8\xff")

        assert url == "/uploads/avatars/test.jpg"
        file_path = local_backend._base / "avatars" / "test.jpg"
        assert file_path.exists()
        assert file_path.read_bytes() == b"\xff\xd8\xff"

    def test_upload_creates_category_dir(self, local_backend):
        """Upload creates the category subdirectory if missing."""
        local_backend.upload("newcat", "file.png", b"\x89PNG")

        cat_dir = local_backend._base / "newcat"
        assert cat_dir.is_dir()

    def test_get_url(self, local_backend):
        """get_url returns the expected local path."""
        url = local_backend.get_url("avatars", "photo.jpg")
        assert url == "/uploads/avatars/photo.jpg"

    def test_delete_removes_file(self, local_backend):
        """Deleting a file removes it from disk."""
        local_backend.upload("tmp", "del.txt", b"data")
        file_path = local_backend._base / "tmp" / "del.txt"
        assert file_path.exists()

        local_backend.delete("tmp", "del.txt")
        assert not file_path.exists()

    def test_delete_nonexistent_is_noop(self, local_backend):
        """Deleting a file that does not exist does not raise."""
        local_backend.delete("missing", "nope.txt")


# ---------------------------------------------------------------------------
# _S3Backend tests (mocked boto3)
# ---------------------------------------------------------------------------


class TestS3Backend:
    """Tests for the S3/R2 storage backend with mocked boto3."""

    def _make_backend(self, monkeypatch):
        """Create an _S3Backend with mocked boto3."""
        mock_client = MagicMock()
        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = mock_client

        monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
        monkeypatch.setenv("S3_ACCESS_KEY_ID", "fake-key")
        monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "fake-secret")
        monkeypatch.setenv("S3_PUBLIC_URL", "https://cdn.example.com")

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            backend = storage_mod._S3Backend("test-bucket")
            backend._client = mock_client

        return backend, mock_client

    def test_is_not_local(self, monkeypatch):
        """S3 backend reports is_local=False."""
        backend, _ = self._make_backend(monkeypatch)
        assert backend.is_local is False

    def test_upload_calls_put_object(self, monkeypatch):
        """Upload delegates to S3 put_object with correct params."""
        backend, mock_client = self._make_backend(monkeypatch)

        url = backend.upload("avatars", "photo.jpg", b"\xff\xd8\xff")

        mock_client.put_object.assert_called_once_with(
            Bucket="test-bucket",
            Key="avatars/photo.jpg",
            Body=b"\xff\xd8\xff",
            ContentType="image/jpeg",
        )
        assert url == "https://cdn.example.com/avatars/photo.jpg"

    def test_upload_png_content_type(self, monkeypatch):
        """Upload detects PNG content type from extension."""
        backend, mock_client = self._make_backend(monkeypatch)

        backend.upload("img", "logo.png", b"\x89PNG")

        call_kwargs = mock_client.put_object.call_args[1]
        assert call_kwargs["ContentType"] == "image/png"

    def test_upload_webp_content_type(self, monkeypatch):
        """Upload detects WebP content type from extension."""
        backend, mock_client = self._make_backend(monkeypatch)

        backend.upload("img", "photo.webp", b"RIFF")

        call_kwargs = mock_client.put_object.call_args[1]
        assert call_kwargs["ContentType"] == "image/webp"

    def test_upload_unknown_extension(self, monkeypatch):
        """Upload uses octet-stream for unknown extensions."""
        backend, mock_client = self._make_backend(monkeypatch)

        backend.upload("docs", "file.xyz", b"data")

        call_kwargs = mock_client.put_object.call_args[1]
        assert call_kwargs["ContentType"] == "application/octet-stream"

    def test_delete_calls_delete_object(self, monkeypatch):
        """Delete delegates to S3 delete_object."""
        backend, mock_client = self._make_backend(monkeypatch)

        backend.delete("avatars", "old.jpg")

        mock_client.delete_object.assert_called_once_with(
            Bucket="test-bucket", Key="avatars/old.jpg"
        )

    def test_get_url(self, monkeypatch):
        """get_url returns the public CDN URL."""
        backend, _ = self._make_backend(monkeypatch)

        url = backend.get_url("avatars", "photo.jpg")
        assert url == "https://cdn.example.com/avatars/photo.jpg"


# ---------------------------------------------------------------------------
# get_storage / _get_backend selection
# ---------------------------------------------------------------------------


class TestGetStorage:
    """Tests for backend selection logic."""

    def test_selects_local_without_env(self, monkeypatch):
        """Without S3_BUCKET_NAME, selects local backend."""
        monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

        backend = storage_mod._get_backend()
        assert backend.is_local is True

    def test_selects_s3_with_env(self, monkeypatch):
        """With S3_BUCKET_NAME set, selects S3 backend."""
        monkeypatch.setenv("S3_BUCKET_NAME", "my-bucket")
        monkeypatch.setenv("S3_ACCESS_KEY_ID", "key")
        monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "secret")

        mock_boto3 = MagicMock()
        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            backend = storage_mod._get_backend()

        assert backend.is_local is False

    def test_get_storage_is_singleton(self, monkeypatch):
        """get_storage returns the same instance on repeated calls."""
        monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

        s1 = storage_mod.get_storage()
        s2 = storage_mod.get_storage()

        assert s1 is s2

    def test_get_storage_lazy_init(self, monkeypatch):
        """get_storage initializes on first call only."""
        monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
        assert storage_mod._storage is None

        result = storage_mod.get_storage()

        assert result is not None
        assert storage_mod._storage is result


# ---------------------------------------------------------------------------
# Content type mapping coverage
# ---------------------------------------------------------------------------


class TestContentTypeMapping:
    """Verify all mapped content types via S3 upload."""

    @pytest.mark.parametrize(
        "filename,expected_ct",
        [
            ("img.jpg", "image/jpeg"),
            ("img.jpeg", "image/jpeg"),
            ("img.png", "image/png"),
            ("img.webp", "image/webp"),
            ("img.gif", "image/gif"),
            ("file.bin", "application/octet-stream"),
        ],
    )
    def test_content_type_detection(self, monkeypatch, filename, expected_ct):
        """Each extension maps to the correct content type."""
        mock_client = MagicMock()
        mock_boto3 = MagicMock()
        mock_boto3.client.return_value = mock_client

        monkeypatch.setenv("S3_BUCKET_NAME", "bucket")
        monkeypatch.setenv("S3_ACCESS_KEY_ID", "k")
        monkeypatch.setenv("S3_SECRET_ACCESS_KEY", "s")

        with patch.dict("sys.modules", {"boto3": mock_boto3}):
            backend = storage_mod._S3Backend("bucket")
            backend._client = mock_client

        backend.upload("cat", filename, b"data")

        call_kwargs = mock_client.put_object.call_args[1]
        assert call_kwargs["ContentType"] == expected_ct
