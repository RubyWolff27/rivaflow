"""Webhook endpoints for external service callbacks."""

import base64
import hashlib
import hmac
import logging

from fastapi import APIRouter, HTTPException, Request, status

from rivaflow.core.services.whoop_service import WhoopService
from rivaflow.core.settings import settings
from rivaflow.db.repositories.whoop_connection_repo import (
    WhoopConnectionRepository,
)

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
logger = logging.getLogger(__name__)

service = WhoopService()
connection_repo = WhoopConnectionRepository()


def _verify_whoop_signature(body: bytes, signature: str, timestamp: str) -> bool:
    """Verify HMAC-SHA256 signature from WHOOP webhook.

    WHOOP signs webhooks with: base64(HMAC-SHA256(timestamp + body, client_secret))
    Headers: X-WHOOP-Signature, X-WHOOP-Signature-Timestamp
    """
    secret = settings.WHOOP_CLIENT_SECRET
    if not secret:
        logger.warning("WHOOP_CLIENT_SECRET not set — cannot verify webhook")
        return False
    message = timestamp.encode() + body
    expected = base64.b64encode(
        hmac.new(secret.encode(), message, hashlib.sha256).digest()
    ).decode()
    return hmac.compare_digest(expected, signature)


def _lookup_user_by_whoop_id(whoop_user_id: str) -> int | None:
    """Find the RivaFlow user_id for a given whoop_user_id."""
    from rivaflow.db.database import convert_query, get_connection

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            convert_query(
                "SELECT user_id FROM whoop_connections " "WHERE whoop_user_id = ? AND is_active = 1"
            ),
            (whoop_user_id,),
        )
        row = cursor.fetchone()
        if row:
            return row["user_id"] if hasattr(row, "keys") else row[0]
    return None


@router.post("/whoop")
async def whoop_webhook(request: Request):
    """Receive and process webhook events from WHOOP.

    This endpoint is NOT JWT-protected — WHOOP calls it directly.
    Authentication is via HMAC signature verification using the
    Client Secret as the signing key.
    """
    # Read raw body for signature verification
    body = await request.body()

    # Verify signature using WHOOP's scheme:
    # base64(HMAC-SHA256(timestamp + body, client_secret))
    secret = settings.WHOOP_CLIENT_SECRET
    if secret:
        signature = request.headers.get("X-WHOOP-Signature", "")
        timestamp = request.headers.get("X-WHOOP-Signature-Timestamp", "")
        if not signature or not _verify_whoop_signature(body, signature, timestamp):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid webhook signature",
            )
    else:
        logger.warning("WHOOP_CLIENT_SECRET not set — skipping signature check")

    # Parse event
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        )

    event_type = payload.get("type", "")
    whoop_user_id = str(payload.get("user_id", ""))

    if not whoop_user_id:
        logger.warning("Webhook missing user_id in payload")
        return {"status": "ignored", "reason": "missing user_id"}

    # Look up internal user
    user_id = _lookup_user_by_whoop_id(whoop_user_id)
    if not user_id:
        logger.info(f"Webhook for unknown whoop_user_id={whoop_user_id}")
        return {"status": "ignored", "reason": "unknown user"}

    # Dispatch based on event type
    try:
        if event_type == "workout.updated":
            service.sync_workouts(user_id, days_back=1)
        elif event_type in ("recovery.updated", "sleep.updated"):
            service.sync_recovery(user_id, days_back=1)
        elif event_type == "body_measurement.updated":
            # Future: sync body measurement
            logger.info(f"body_measurement.updated for user {user_id} (not yet handled)")
        else:
            logger.info(f"Unhandled WHOOP event type: {event_type}")
    except Exception:
        logger.error(
            f"Error processing webhook {event_type} for user {user_id}",
            exc_info=True,
        )

    # Always return 200 — WHOOP expects fast response
    return {"status": "ok"}
