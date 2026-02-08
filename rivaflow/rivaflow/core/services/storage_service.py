"""File storage service with local and S3/R2 backends.

Uses local filesystem in development, S3-compatible storage (AWS S3 or
Cloudflare R2) in production. Backend is selected automatically based on
whether S3_BUCKET_NAME is set.
"""

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_backend():
    """Return the appropriate storage backend based on environment."""
    bucket = os.getenv("S3_BUCKET_NAME")
    if bucket:
        return _S3Backend(bucket)
    return _LocalBackend()


class _LocalBackend:
    """Store files on local disk (development only)."""

    def __init__(self):
        base = Path(__file__).parent.parent.parent.parent / "uploads"
        base.mkdir(parents=True, exist_ok=True)
        self._base = base

    def upload(self, category: str, filename: str, content: bytes) -> str:
        """Save file and return URL path."""
        dest = self._base / category
        dest.mkdir(parents=True, exist_ok=True)
        file_path = dest / filename
        with open(file_path, "wb") as f:
            f.write(content)
        return f"/uploads/{category}/{filename}"

    def delete(self, category: str, filename: str) -> None:
        """Delete file from disk."""
        file_path = self._base / category / filename
        if file_path.exists():
            file_path.unlink()

    def get_url(self, category: str, filename: str) -> str:
        """Return local URL path."""
        return f"/uploads/{category}/{filename}"

    @property
    def is_local(self) -> bool:
        return True


class _S3Backend:
    """Store files in an S3-compatible bucket (AWS S3 or Cloudflare R2)."""

    def __init__(self, bucket: str):
        import boto3

        self._bucket = bucket
        self._public_url = os.getenv(
            "S3_PUBLIC_URL", f"https://{bucket}.s3.amazonaws.com"
        )

        kwargs = {
            "aws_access_key_id": os.getenv("S3_ACCESS_KEY_ID"),
            "aws_secret_access_key": os.getenv("S3_SECRET_ACCESS_KEY"),
        }
        endpoint = os.getenv("S3_ENDPOINT_URL")
        if endpoint:
            kwargs["endpoint_url"] = endpoint

        region = os.getenv("S3_REGION", "auto")
        kwargs["region_name"] = region

        self._client = boto3.client("s3", **kwargs)

    def upload(self, category: str, filename: str, content: bytes) -> str:
        """Upload file to S3 and return public URL."""
        key = f"{category}/{filename}"

        # Guess content type
        ext = Path(filename).suffix.lower()
        content_types = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".webp": "image/webp",
            ".gif": "image/gif",
        }
        content_type = content_types.get(ext, "application/octet-stream")

        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=content,
            ContentType=content_type,
        )
        logger.info(f"Uploaded {key} to S3 bucket {self._bucket}")
        return f"{self._public_url}/{key}"

    def delete(self, category: str, filename: str) -> None:
        """Delete file from S3."""
        key = f"{category}/{filename}"
        self._client.delete_object(Bucket=self._bucket, Key=key)
        logger.info(f"Deleted {key} from S3 bucket {self._bucket}")

    def get_url(self, category: str, filename: str) -> str:
        """Return public URL for the file."""
        return f"{self._public_url}/{category}/{filename}"

    @property
    def is_local(self) -> bool:
        return False


# Module-level singleton, lazily initialised
_storage = None


def get_storage():
    """Get the storage backend (singleton)."""
    global _storage
    if _storage is None:
        _storage = _get_backend()
        backend_type = "local" if _storage.is_local else "S3"
        logger.info(f"Storage backend initialised: {backend_type}")
    return _storage
