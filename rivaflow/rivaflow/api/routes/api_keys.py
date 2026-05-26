"""API key management endpoints (feat/api-keys).

Per-user API keys with user-equivalent permissions. Raw key returned exactly
once at creation; thereafter only metadata + the display prefix are visible.
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.models import (
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyMetadata,
)
from rivaflow.db.repositories.api_key_repo import ApiKeyRepository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/api-keys",
    response_model=list[ApiKeyMetadata],
    tags=["api-keys"],
)
@route_error_handler("list_api_keys", detail="Failed to list API keys")
def list_api_keys(current_user: dict = Depends(get_current_user)) -> list[dict]:
    """List the authenticated user's API keys (active + revoked).

    Never returns the raw key. To see the actual value of a key, you must
    generate a new one — old raw values are deliberately unrecoverable.
    """
    user_id: int = current_user["id"]
    return ApiKeyRepository.list_by_user(user_id)


@router.post(
    "/api-keys",
    response_model=ApiKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["api-keys"],
)
@route_error_handler("create_api_key", detail="Failed to create API key")
def create_api_key(
    req: ApiKeyCreate,
    current_user: dict = Depends(get_current_user),
) -> dict:
    """Generate a new API key.

    The raw key value is returned EXACTLY ONCE in this response. The server
    only persists a SHA-256 hash. Subsequent list/get calls never include the
    raw value.

    Use the returned key as an HTTP Bearer credential:

        Authorization: Bearer rf_pk_<the-key>

    Keys carry the same authorization as the issuing user.
    """
    user_id: int = current_user["id"]
    raw_key = ApiKeyRepository.generate_raw_key()
    row = ApiKeyRepository.create(user_id=user_id, name=req.name, raw_key=raw_key)
    if not row:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to persist API key",
        )
    logger.info(
        "API key created — user_id=%s name=%s prefix=%s",
        user_id,
        req.name,
        row["key_prefix"],
    )
    return {**row, "raw_key": raw_key}


@router.delete(
    "/api-keys/{api_key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["api-keys"],
)
@route_error_handler("revoke_api_key", detail="Failed to revoke API key")
def revoke_api_key(
    api_key_id: int,
    current_user: dict = Depends(get_current_user),
) -> None:
    """Revoke an API key.

    Idempotent: revoking an already-revoked or non-existent key returns 404 so
    the client knows there was no live key to revoke.
    """
    user_id: int = current_user["id"]
    ok = ApiKeyRepository.revoke(api_key_id, user_id)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found or already revoked",
        )
    logger.info("API key revoked — id=%s user_id=%s", api_key_id, user_id)
    return None
