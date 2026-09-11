

from __future__ import annotations

import json
from pathlib import Path

import pytest

from adapters.mock_transcriber import MockTranscriptionProvider
from services.transcription_port import TranscriptionPermanentError


REPO = Path(__file__).resolve().parent.parent 


def make_provider(**overrides: object) -> MockTranscriptionProvider:
    return MockTranscriptionProvider(REPO / "recordings", **overrides)  # type: ignore[arg-type]


def test_selects_recording_by_stem() -> None:
    result = make_provider().transcribe(b"ignored bytes", language="auto", filename="bn_bill_01.wav")
    assert result.language == "bn"
    assert result.transcript.startswith("বিলটা")
    assert result.provider == "mock"
    assert result.no_speech is False
    assert result.duration_seconds > 0


def test_unknown_stem_falls_back_to_silence() -> None:
    result = make_provider().transcribe(b"", language="bn", filename="mystery_upload.mp3")
    assert result.no_speech is True
    assert result.transcript == ""


def test_stem_ignores_directory_parts() -> None:
    result = make_provider().transcribe(b"", language="auto", filename="/tmp/uploads/en_check_01.webm")
    assert result.language == "en"


def test_malformed_recording_raises_permanent(tmp_path: Path) -> None:
    (tmp_path / "broken.json").write_text("{ not json", encoding="utf-8")
    provider = MockTranscriptionProvider(tmp_path, default_recording="broken.json")
    with pytest.raises(TranscriptionPermanentError):
        provider.transcribe(b"", language="auto", filename="anything.wav")


def test_recording_language_must_be_concrete(tmp_path: Path) -> None:
    (tmp_path / "auto.json").write_text(
        json.dumps({"transcript": "x", "language": "auto", "duration_seconds": 1.0}),
        encoding="utf-8",
    )
    provider = MockTranscriptionProvider(tmp_path, default_recording="auto.json")
    with pytest.raises(TranscriptionPermanentError):
        provider.transcribe(b"", language="auto", filename="whatever.wav")