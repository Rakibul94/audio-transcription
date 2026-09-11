
from __future__ import annotations

from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    """A completed transcription, as clients see it.

    Promises:
    - transcript is VERBATIM model output: original casing spacing and punctuation preserved.
    - language is always concrete ("bn"/"en") even when the request said
      "auto" — detection is resolved before this model is built.
    - Silence is a VALID answer: no_speech=True with transcript="" is a
      200, never an error. A quiet room is not a server fault.
    - segments are deliberately absent: no_speech_prob and avg_logprob
      are internal policy signals (Phase 5), not client API.
    """
    warnings: list[str] = []

    transcript: str
    language: str
    duration_seconds: float
    no_speech: bool
    provider: str
    format: str