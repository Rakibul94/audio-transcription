

from __future__ import annotations


from adapters.mock_transcriber import MockTranscriptionProvider
from services.config import Settings
from services.transcription_port import TranscriptionProvider


def create_transcription_provider(settings: Settings) -> TranscriptionProvider:
    if settings.provider == "mock":
        return MockTranscriptionProvider(
            settings.recordings_dir,
            default_recording=settings.default_recording,
        )

    if settings.provider == "fasterwhisper":
        from adapters.fasterwhisper_transcriber import FasterWhisperProvider
        return FasterWhisperProvider(
            model_size=settings.whisper_model,
            cpu_threads=settings.whisper_cpu_threads,
            compute_type=settings.whisper_compute_type,
            model_dir=settings.whisper_model_dir,
            download=settings.whisper_download,
            beam_size=settings.whisper_beam_size,
            initial_prompt=settings.whisper_initial_prompt,
        )
    raise ValueError(f"Provider {settings.provider!r} is not wired yet")
    