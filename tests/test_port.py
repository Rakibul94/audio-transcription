

from __future__ import annotations
from dataclasses import FrozenInstanceError

import pytest

from services.transcription_port import (
    TranscriptionPermanentError,
    TranscriptionProviderError,
    TranscriptionResult,
    TranscriptionTemporaryError,
)


def test_result_is_frozen() -> None:
    result = TranscriptionResult(
        transcript="", language="bn", duration_seconds=3.0, provider="mock"
    )
    with pytest.raises(FrozenInstanceError):
        result.transcript = "mutated"  # type: ignore[misc]


def test_defaults_match_no_speech_contract() -> None:
    result = TranscriptionResult(
        transcript="", language="en", duration_seconds=1.0, provider="mock", no_speech=True
    )
    assert result.no_speech is True
    assert result.segments == ()


def test_error_hierarchy_is_catchable_at_the_base() -> None:
    assert issubclass(TranscriptionTemporaryError, TranscriptionProviderError)
    assert issubclass(TranscriptionPermanentError, TranscriptionProviderError)