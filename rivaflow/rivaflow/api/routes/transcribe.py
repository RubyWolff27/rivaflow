"""Audio transcription endpoint using OpenAI Whisper API."""

import logging

import httpx
from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import JSONResponse

from rivaflow.api.rate_limit import limiter
from rivaflow.core.dependencies import get_current_user
from rivaflow.core.error_handling import route_error_handler
from rivaflow.core.settings import settings

router = APIRouter(prefix="/transcribe", tags=["transcribe"])
logger = logging.getLogger(__name__)

CLEANUP_PROMPT = (
    "Clean up this voice transcript for BJJ training session notes. "
    "Fix punctuation and capitalization. Remove filler words "
    "(um, uh, like, you know, so yeah, basically). "
    "Keep the original wording and meaning — do not rephrase, "
    "summarize, or add anything. Return only the cleaned text."
)

ALLOWED_MIME_TYPES = {
    "audio/webm",
    "audio/mp4",
    "audio/mpeg",
    "audio/mp3",
    "audio/wav",
    "audio/ogg",
    "audio/x-m4a",
    "video/webm",
}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB

# File extension mapping for content types
MIME_TO_EXT = {
    "audio/webm": "webm",
    "video/webm": "webm",
    "audio/mp4": "mp4",
    "audio/mpeg": "mp3",
    "audio/mp3": "mp3",
    "audio/wav": "wav",
    "audio/ogg": "ogg",
    "audio/x-m4a": "m4a",
}


@router.post("/")
@limiter.limit("20/minute")
@route_error_handler("transcribe_audio", detail="Transcription failed")
async def transcribe_audio(
    request: Request,
    file: UploadFile,
    current_user: dict = Depends(get_current_user),
):
    """Transcribe uploaded audio using OpenAI Whisper API.

    Accepts audio files (webm, mp4, mp3, wav, ogg) up to 25MB.
    Returns the transcribed text.
    """
    api_key = settings.OPENAI_API_KEY
    if not api_key:
        return JSONResponse(
            status_code=503,
            content={"detail": "Transcription service not configured."},
        )

    # Validate MIME type
    content_type = (file.content_type or "").split(";")[0].strip()
    if content_type not in ALLOWED_MIME_TYPES:
        return JSONResponse(
            status_code=400,
            content={
                "detail": f"Unsupported audio format: {content_type}. "
                "Supported: webm, mp4, mp3, wav, ogg."
            },
        )

    # Read and validate size
    audio_data = await file.read()
    if len(audio_data) == 0:
        return JSONResponse(
            status_code=400,
            content={"detail": "Empty audio file."},
        )
    if len(audio_data) > MAX_FILE_SIZE:
        return JSONResponse(
            status_code=400,
            content={"detail": "Audio file too large. Maximum 25MB."},
        )

    # Determine filename with extension for Whisper
    ext = MIME_TO_EXT.get(content_type, "webm")
    filename = f"audio.{ext}"

    # Proxy to OpenAI Whisper API
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (filename, audio_data, content_type)},
                data={"model": "whisper-1"},
            )

        if response.status_code != 200:
            logger.error(
                "Whisper API error: %s %s",
                response.status_code,
                response.text[:200],
            )
            return JSONResponse(
                status_code=502,
                content={"detail": "Transcription service error."},
            )

        result = response.json()
        transcript = result.get("text", "").strip()

        if not transcript:
            return JSONResponse(
                status_code=200,
                content={"transcript": ""},
            )

        # Clean up transcript with gpt-4o-mini
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                cleanup_resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": CLEANUP_PROMPT},
                            {"role": "user", "content": transcript},
                        ],
                        "temperature": 0,
                        "max_tokens": 1024,
                    },
                )
            if cleanup_resp.status_code == 200:
                cleaned = (
                    cleanup_resp.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                if cleaned:
                    transcript = cleaned
        except Exception:
            logger.debug("Transcript cleanup failed, using raw Whisper output")

        return JSONResponse(
            status_code=200,
            content={"transcript": transcript},
        )

    except httpx.TimeoutException:
        logger.warning("Whisper API timeout")
        return JSONResponse(
            status_code=504,
            content={"detail": "Transcription timed out. Please try again."},
        )
    except Exception:
        logger.exception("Unexpected transcription error")
        return JSONResponse(
            status_code=500,
            content={"detail": "Transcription failed. Please try again."},
        )
