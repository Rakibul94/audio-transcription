

from __future__ import annotations

import json
import logging
from pathlib import Path

from services.transcription_port import (
    Segment,
    TranscriptionPermanentError,
    TranscriptionProvider,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


class MockTranscriptionProvider(TranscriptionProvider):
    """Replays recorded provider responses: zero network, zero model load.

    Recording selection: if "<stem>.json" matches the uploaded filename,
    play that recording; otherwise degrade to the default (silence). The
    uploaded bytes are never decoded — the filename is the scenario
    switch used by demos and tests.

    The language hint is ignored: a recording is recorded truth, and a
    hint does not rewrite history. Callers learn the real language from
    the result.
    """

    def __init__(
        self, recordings_dir: str | Path, default_recording: str = "silence.json"
    ) -> None:
        self.recordings_dir = Path(recordings_dir)
        self.default_recording = self.recordings_dir / default_recording

    def transcribe(
        self, audio: bytes, *, language: str, filename: str = ""
    ) -> TranscriptionResult:
        stem = Path(filename).stem or "default"
        recording_path = self._select_recording(stem)
        logger.info("MOCK ASR: %s -> %s (audio bytes ignored)", filename, recording_path.name)
        return self._load(recording_path)

    def _select_recording(self, stem: str) -> Path:
        candidate = self.recordings_dir / f"{stem}.json"
        if candidate.is_file():
            return candidate
        logger.warning(
            "MOCK ASR: no recording %r - unknown filename degrades to the silence default",
            candidate.name,
        )
        return self.default_recording

    def _load(self, recording_path: Path) -> TranscriptionResult:
        try:
            recording = json.loads(recording_path.read_text(encoding="utf-8"))
            language = str(recording["language"])
            if language not in {"bn", "en"}:
                raise ValueError(f"language {language!r} is not concrete (bn|en)")
            segments = tuple(
                Segment(
                    text=str(entry["text"]),
                    no_speech_prob=float(entry["no_speech_prob"]),
                    avg_logprob=float(entry["avg_logprob"]),
                )
                for entry in recording.get("segments", ())
            )
            return TranscriptionResult(
                transcript=str(recording["transcript"]),
                language=language,
                duration_seconds=float(recording["duration_seconds"]),
                provider="mock",
                no_speech=bool(recording.get("no_speech", False)),
                segments=segments,
            )
        except (OSError, KeyError, TypeError, ValueError) as error:
            raise TranscriptionPermanentError(
                f"Malformed recording: {recording_path} ({error})"
            ) from error