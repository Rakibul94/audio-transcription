

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Language = Literal["bn", "en", "auto"]


class TranscriptionProviderError(Exception):
    """Base class for every transcription provider failure."""


class TranscriptionTemporaryError(TranscriptionProviderError):
    """Retryable failure: timeout, throttling, transient decode error."""


class TranscriptionPermanentError(TranscriptionProviderError):
    """Non-retryable failure: corrupt audio, undecodable container, bad credentials."""


@dataclass(frozen=True)
class Segment:
    """One decoded speech segment, carrying only the confidence signals the
    no-speech policy needs (services/) — SDK types never cross this boundary.
    Whisper's no_speech_prob / avg_logprob land here as plain floats.
    """

    text: str
    no_speech_prob: float
    avg_logprob: float


@dataclass(frozen=True)
class TranscriptionResult:
    

    transcript: str
    language: str
    duration_seconds: float
    provider: str                  # adapter self-identifies: "mock" | "fasterwhisper"
    no_speech: bool = False
    segments: tuple[Segment, ...] = ()


class TranscriptionProvider(ABC):
    """The boundary services/ codes against. Implementations live in adapters/."""

    @abstractmethod
    def transcribe(
        self, audio: bytes, *, language: Language, filename: str = ""
    ) -> TranscriptionResult:
        """Transcribe one audio file.

        Promises:
        - language must already be validated by the caller ("bn" / "en" / "auto").
        - Returns TranscriptionResult; raises only TranscriptionProviderError
          subclasses — never a raw SDK exception.
        - filename is metadata for the mock (recording selection by stem);
          real adapters may ignore it.
        """