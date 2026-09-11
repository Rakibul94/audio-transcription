

from __future__ import annotations

import logging

from fastapi import APIRouter, File, Form, UploadFile, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from services.transcription_port import (
    TranscriptionPermanentError,
    TranscriptionTemporaryError,
)
from services.audio_format import sniff_audio_format
from services.config import Settings
from api.schemas import TranscriptionResponse

from services.transcription_service import TranscriptionService

logger = logging.getLogger(__name__)

CHUNK_SIZE = 1024 * 1024  # 1 MiB: large enough to be fast, small enough to abort early



def create_router(service: TranscriptionService, settings: Settings) -> APIRouter:

    """Build the transcription routes.

    Dependencies are injected, never imported: tests pass a mock-backed
    service and shrunken settings (tiny upload caps, restricted
    languages) through this same factory.
    """

    router = APIRouter(prefix="/api/v1", tags=["transcription"])

    @router.post("/transcribe", response_model=TranscriptionResponse)
    async def transcribe(
        file: UploadFile = File(...),
        language: str = Form("auto"),
    ) -> TranscriptionResponse:
       
        if language not in settings.allowed_languages:
            raise HTTPException(422, f"language {language!r} is not supported")

        buf = bytearray()
        while chunk := await file.read(CHUNK_SIZE):
             buf += chunk
             if len(buf) > settings.max_upload_bytes:
                 raise HTTPException(413, "audio exceeds the upload limit")

        # 3. Sniff: magic bytes decide; the extension gets no vote.
        #    An empty file also lands here — no bytes, no magic, no format.
        fmt = sniff_audio_format(bytes(buf))
        if fmt is None:
            raise HTTPException(415, "could not determine audio format from file content")
        if fmt not in settings.allowed_formats:
            raise HTTPException(415, f"{fmt!r} audio is not an allowed format")

        filename = file.filename or ""
        try:
            result = await run_in_threadpool(
                service.transcribe, bytes(buf), language=language, filename=filename
            )
        except TranscriptionPermanentError as e:
            raise HTTPException(502, f"transcription provider failed: {e}") from e
        except TranscriptionTemporaryError as e:
            raise HTTPException(504, f"transcription provider timed out: {e}") from e
        logger.info(
            "transcribed %s [%s->%s] %.2fs no_speech=%s",
            filename or "<upload>", language, result.language,
            result.duration_seconds, result.no_speech,
        )
        warnings: list[str] = []
        if result.no_speech:
            warnings.append("No speech detected — transcript is empty.")
        if language in {"bn", "en"} and result.language != language:
            warnings.append(
                f"Detected language {result.language!r} differs from requested {language!r}."
            )
        return TranscriptionResponse(
            transcript=result.transcript,
            language=result.language,
            duration_seconds=result.duration_seconds,
            no_speech=result.no_speech,
            provider=result.provider,
            format=fmt,
        )

    return router