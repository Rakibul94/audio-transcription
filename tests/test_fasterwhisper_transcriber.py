

from __future__ import annotations

import sys

import pytest

from adapters.fasterwhisper_transcriber import FasterWhisperProvider
from services.transcription_port import TranscriptionPermanentError


class FakeSegment:
    def __init__(
        self, text: str, no_speech_prob: float = 0.05, avg_logprob: float = -0.2
    ) -> None:
        self.text = text
        self.no_speech_prob = no_speech_prob
        self.avg_logprob = avg_logprob


class FakeInfo:
    def __init__(self, language: str = "bn", duration: float = 6.2) -> None:
        self.language = language
        self.duration = duration


class FakeModel:
    """Records the transcribe() kwargs; replays canned segments."""

    def __init__(self, segments=(), info=None, error: Exception | None = None) -> None:
        self.segments = list(segments)
        self.info = info or FakeInfo()
        self.error = error
        self.calls: list[dict] = []

    def transcribe(self, audio, *, language=None, **kwargs):
        self.calls.append({"language": language, **kwargs})
        if self.error:
            raise self.error
        return iter(self.segments), self.info


def make_provider(model: FakeModel) -> FasterWhisperProvider:
    return FasterWhisperProvider(_model=model)  # test seam: SDK never loaded


def test_importing_the_adapter_does_not_import_the_sdk() -> None:
    # The lazy-import contract, checked mechanically.
    assert "faster_whisper" not in sys.modules


def test_maps_segments_and_preserves_verbatim_text() -> None:
    model = FakeModel(segments=[FakeSegment(" বিলটা"), FakeSegment(" পঁচিশ টাকা")])
    result = make_provider(model).transcribe(b"x", language="bn")
    assert result.transcript == "বিলটা পঁচিশ টাকা"
    assert result.provider == "fasterwhisper"
    assert [s.no_speech_prob for s in result.segments] == [0.05, 0.05]


def test_auto_passes_none_explicit_passes_language() -> None:
    model = FakeModel()
    make_provider(model).transcribe(b"x", language="auto")
    make_provider(model).transcribe(b"x", language="en")
    assert [c["language"] for c in model.calls] == [None, "en"]


def test_cpu_levers_are_passed() -> None:
    model = FakeModel()
    make_provider(model).transcribe(b"x", language="auto")
    call = model.calls[0]
    assert call["vad_filter"] is True
    assert call["beam_size"] == 5
    assert call["condition_on_previous_text"] is False
    assert call["vad_parameters"] == {"min_silence_duration_ms": 500}


def test_zero_segments_is_valid_no_speech() -> None:
    result = make_provider(FakeModel(segments=[])).transcribe(b"x", language="auto")
    assert result.no_speech is True
    assert result.transcript == ""
    assert result.language == "bn"  # detected anyway — silence still has a language guess


def test_off_target_language_is_returned_with_a_warning(caplog: pytest.LogCaptureFixture) -> None:
    model = FakeModel(info=FakeInfo(language="hi"))
    with caplog.at_level("WARNING"):
        result = make_provider(model).transcribe(b"x", language="auto")
    assert result.language == "hi"
    assert any("hi" in r.message for r in caplog.records)


def test_decode_failure_raises_permanent() -> None:
    model = FakeModel(error=RuntimeError("could not load audio"))
    with pytest.raises(TranscriptionPermanentError):
        make_provider(model).transcribe(b"x", language="auto")