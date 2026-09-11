

from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Any

from services.transcription_port import (
    Segment,
    TranscriptionPermanentError,
    TranscriptionProvider,
    TranscriptionResult,
)

logger = logging.getLogger(__name__)


class FasterWhisperProvider(TranscriptionProvider):
    """Real ASR: faster-whisper (CTranslate2) on CPU, int8.

    faster_whisper is imported INSIDE __init__ — importing this module
    must never require the SDK, so a mock-only install keeps working and
    the layering test stays honest (DECISIONS.md #1).

    CPU levers, each documented in DECISIONS.md:
    - compute_type="int8": ~3x faster than float32 on CPU, negligible
      accuracy loss — the standard CPU deployment trick.
    - beam_size=1: greedy decoding; the biggest cheap CPU saving.
    - vad_filter=True: Silero VAD (bundled) skips silence — and doubles
      as the no-speech detector: zero surviving segments == no speech.
    """

    def __init__(
        self,
        model_size: str = "medium",
        cpu_threads: int = 4,
        compute_type: str = "int8",
        model_dir: str | Path | None = None,
        download: bool = True,
        beam_size: int = 5,
        initial_prompt: str | None = None,
        _model: Any = None,
    ) -> None:
        self._beam_size = beam_size         
        self._initial_prompt = initial_prompt
        if _model is not None:
            self._model = _model
            return

        from faster_whisper import WhisperModel  # lazy: only when selected

        common = {"device": "cpu", "compute_type": compute_type, "cpu_threads": cpu_threads}
        if download:
            # Online mode: weights download ONCE at startup into
            # model_dir (or the huggingface cache when None) — never on
            # the request path.
            self._model = WhisperModel(
                model_size,
                download_root=str(model_dir) if model_dir else None,
                **common,
            )
        else:
            if model_dir is None:
                raise ValueError(
                    "whisper_download=false requires whisper_model_dir "
                    "(pre-baked weights, e.g. a Docker volume)"
                )
            # Offline mode: pre-baked weights only — no network ever.
            self._model = WhisperModel(str(model_dir), local_files_only=True, **common)

    def transcribe(
        self, audio: bytes, *, language: str, filename: str = ""
    ) -> TranscriptionResult:
        lang_param = None if language == "auto" else language
        try:
            segment_iter, info = self._model.transcribe(
                io.BytesIO(audio),  # PyAV decodes mp3/m4a/webm — no system ffmpeg
                language=lang_param,
                vad_filter=True,
                vad_parameters={"min_silence_duration_ms": 500},
                beam_size=self._beam_size,
                condition_on_previous_text=False,  # stops cross-segment language drift
                initial_prompt=(
                    self._initial_prompt
                    if self._initial_prompt and lang_param in (None, "bn")
                    else None
                )
            )
            # segment_iter is a generator: iteration is where the CPU
            # work actually happens, so the decode errors surface HERE.
            segments = tuple(
                Segment(
                    text=str(s.text),
                    no_speech_prob=float(s.no_speech_prob),
                    avg_logprob=float(s.avg_logprob),
                )
                for s in segment_iter
            )
        except (RuntimeError, ValueError, OSError) as error:
            # Corrupt audio, undecodable container, bad seek: the bytes
            # are the problem and retrying will not help. A local CPU
            # model has no network to be flaky — TranscriptionTemporary-
            # Error stays reserved for future remote adapters.
            logger.warning("faster-whisper rejected %r: %s", filename, error)
            raise TranscriptionPermanentError(
                f"audio could not be decoded: {error}"
            ) from error

        detected = str(info.language)
        if detected not in {"bn", "en"}:
            # Off-target detection is still reported honestly; deciding
            # what an unexpected language MEANS is the caller's job.
            logger.warning(
                "detected language %r (outside bn/en) for %r", detected, filename
            )

        # VAD filtered everything <=> zero segments survived — that IS
        # the no-speech signal. Phase 5's policy refines it per-segment.
        no_speech = len(segments) == 0
        # VERBATIM inside: faster-whisper segments carry their own leading
        # spaces, so plain concatenation preserves the model's spacing;
        # only the meaningless outer whitespace is trimmed.
        transcript = "".join(s.text for s in segments).strip()

        return TranscriptionResult(
            transcript=transcript,
            language=detected,
            duration_seconds=float(info.duration),
            provider="fasterwhisper",
            no_speech=no_speech,
            segments=segments,
        )