
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration. Every knob is an env var with the ASR_ prefix
    (e.g. ASR_PROVIDER=fasterwhisper). The defaults describe the zero-
    credential, zero-download mock path — exactly what docker compose
    boots with no .env present."""

    model_config = SettingsConfigDict(env_prefix="ASR_", env_file=".env", extra="ignore")

    app_name: str = "audio-transcription"

    # --- provider wiring: which adapter runs is configuration, not code ---
    provider: str = "mock"  # "mock" | "fasterwhisper"
    recordings_dir: str = "recordings"
    default_recording: str = "silence.json"

    # --- upload validation ---
    max_upload_bytes: int = 25 * 1024 * 1024  # the brief's 25 MB cap
    allowed_languages: set[str] = {"bn", "en", "auto"}
    allowed_formats: set[str] = {"wav", "mp3", "ogg", "flac", "m4a", "webm"}

    # --- faster-whisper knobs (read only when provider=fasterwhisper) ---
    whisper_model: str = "medium"
    whisper_compute_type: str = "int8"
    whisper_cpu_threads: int = 4
    whisper_beam_size: int = 5
    whisper_model_dir: str | None = None
    whisper_download: bool = True
    whisper_initial_prompt: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()