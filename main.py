

from __future__ import annotations

import logging

from fastapi import FastAPI

from adapters.factory import create_transcription_provider
from api.routes import create_router
from services.config import Settings, get_settings
from services.transcription_service import TranscriptionService


logging.basicConfig(level=logging.INFO)


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title=settings.app_name)

    provider = create_transcription_provider(settings)
    service = TranscriptionService(provider)
    app.include_router(create_router(service, settings))

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "provider": settings.provider}

    return app


app = create_app()