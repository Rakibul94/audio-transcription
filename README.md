
# audio-transcription

Bilingual (Bangla/English) audio transcription service, CPU-only, built with
FastAPI + faster-whisper. Ships with a mock provider so the whole API can run
and be tested with zero model downloads.

## How to run

**Requirements:** Python 3.11+

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows
pip install -e ".[whisper,dev]"   # or just pip install -e . for mock-only

# Mock mode (default, no model download):
uvicorn main:app --reload

# Real transcription mode:
copy .env.example .env            # sets ASR_PROVIDER=fasterwhisper
uvicorn main:app --reload
```

Docker:

```bash
docker compose up --build         # serves on :8000, caches whisper models in a volume
```

Try it:

```bash
curl -X POST http://localhost:8000/api/v1/transcribe \
  -F "file=@testdata/bangla_alien_podcast.m4a" -F "language=bn"
```

Endpoints: `POST /api/v1/transcribe` (multipart `file` + `language`:
`bn|en|auto`), `GET /health`. Uploads are capped at 25 MB; accepted formats
(wav, mp3, ogg, flac, m4a, webm) are sniffed from file content, not extension.

Run tests: `pytest` · lint: `ruff check .` · types: `mypy .`

## Architecture

```
api/routes.py          HTTP layer: validation (language, size, format sniffing),
                       error mapping (413/415/422/502/504), warnings
services/transcription_service.py
                       Business policy: no-speech / hallucination filtering
services/transcription_port.py
                       Abstract TranscriptionProvider + shared result types
adapters/mock_transcriber.py      fake provider (replays recordings/*.json)
adapters/fasterwhisper_transcriber.py
                                  real provider (lazy-imported)
adapters/factory.py               picks the adapter from Settings
```

**Why this shape:**

- **Ports & adapters** — the service layer codes only against the
  `TranscriptionProvider` interface. The provider is *configuration*, not code:
  `ASR_PROVIDER=mock|fasterwhisper`. This let me build and test the entire HTTP
  pipeline before the model ever ran.
- **The mock is a first-class adapter** — it keys canned responses off the
  uploaded filename stem (`recordings/*.json`) and ignores audio bytes, giving
  deterministic end-to-end tests with no GPU/network.
- **Hallucination policy lives in the service, not the adapter** — silence
  detection (`services/no_speech.py`) treats a segment as junk when
  `no_speech_prob >= 0.90 && avg_logprob <= -1.5`, or `avg_logprob <= -2.5`
  outright. Empty transcripts are returned as `no_speech: true`, never as a
  hallucinated "Thank you."
- **Heavy deps are optional extras** — `pip install -e .` works without
  faster-whisper; the import happens only inside the real adapter.

## Test data and why

- `testdata/bangla_alien_podcast.m4a` — a phone recording of a YouTube video
  containing Bangla speech (with some English code-switching), paired with a
  hand-written reference transcript in `testdata/manifest.json`. It is real
  continuous speech, so it exercises the real adapter the way users will:
  m4a container, natural pace, mixed vocabulary.
- `recordings/*.json` — four hand-written scenarios for the mock provider,
  covering the four outcomes that matter: clean English, clean Bangla, pure
  silence, and ambient noise that makes the model hallucinate "Thank you."
  Together they let the full route + policy stack be tested deterministically.

## Known limitations

- **Code-switching fails.** The model cannot transcribe English and Bangla from
  the *same* audio; it works when the language is assigned explicitly
  (`language=bn` or `en`), but mixed-language audio degrades badly.
- **Accuracy drift.** Transcription is reasonable for the first few seconds,
  then produces text unrelated to the audio — a symptom of CPU-only inference
  with `large-v3-turbo` at `int8`. `small`/`medium` were tried and were worse.
- No GPU support; a stronger model on GPU would improve both problems.
- Mock provider matches by filename stem only — audio content is never analysed.


