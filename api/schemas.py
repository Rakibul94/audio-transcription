
from __future__ import annotations

from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
  
    warnings: list[str] = []

    transcript: str
    language: str
    duration_seconds: float
    no_speech: bool
    provider: str
    format: str