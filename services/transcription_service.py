
from __future__ import annotations

import logging
from dataclasses import replace

from services.no_speech import is_no_speech
from services.transcription_port import (
    Language,
    TranscriptionProvider,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


class TranscriptionService:
   

    def __init__(self, provider: TranscriptionProvider) -> None:
        self._provider = provider

    def transcribe(
        self, audio: bytes, *, language: Language, filename: str = ""
    ) -> TranscriptionResult:
        result = self._provider.transcribe(audio, language=language, filename=filename)

        # Zero segments == VAD filtered everything: that IS the silence
        # signal for both adapters.
        vad_filtered_all = len(result.segments) == 0
        if is_no_speech(result.segments, vad_filtered_all=vad_filtered_all):
            if result.transcript:
                logger.info(
                    "no-speech policy wiped %d hallucinated segment(s) for %r",
                    len(result.segments),
                    filename,
                )
            return replace(result, transcript="", no_speech=True)
        return replace(result, no_speech=False)