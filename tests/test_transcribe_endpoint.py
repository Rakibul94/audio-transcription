
from __future__ import annotations

from conftest import build_client
from fastapi.testclient import TestClient
from httpx import Response

# Sniffing runs BEFORE the provider, so every endpoint test payload
# needs real magic bytes — even though the mock ignores the audio.
FAKE_WAV = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 64
FAKE_MP3 = b"ID3" + b"\x00" * 64


def post(
    client: TestClient, filename: str, payload: bytes, language: str = "auto"
) -> Response:
    return client.post(
        "/api/v1/transcribe",
        files={"file": (filename, payload, "application/octet-stream")},
        data={"language": language},
    )


def test_bn_happy_path_replays_recording() -> None:
    response = post(build_client(), "bn_bill_01.wav", FAKE_WAV, language="bn")
    assert response.status_code == 200
    body = response.json()
    assert body["language"] == "bn"
    assert body["transcript"].startswith("বিলটা")
    assert body["no_speech"] is False
    assert "segments" not in body  # internal policy signal, not API


def test_auto_defaults_and_resolves_concrete_language() -> None:
    response = post(build_client(), "en_check_01.mp3", FAKE_MP3)
    assert response.status_code == 200
    assert response.json()["language"] == "en"


def test_invalid_language_is_structured_422() -> None:
    response = post(build_client(), "bn_bill_01.wav", FAKE_WAV, language="fr")
    assert response.status_code == 422
    assert "not supported" in response.json()["detail"]

def test_oversize_aborts_with_413() -> None:
    response = post(build_client(max_upload_bytes=8), "big.wav", FAKE_WAV)
    assert response.status_code == 413
    assert "exceeds" in response.json()["detail"]


def test_exact_limit_boundary_passes() -> None:
    payload = b"ID3" + b"\x00" * 5  # exactly 8 bytes
    response = post(build_client(max_upload_bytes=8), "bn_bill_01.mp3", payload)
    assert response.status_code == 200


def test_bad_magic_bytes_are_415() -> None:
    response = post(build_client(), "recording.wav", b"definitely not audio")
    assert response.status_code == 415
    assert "format" in response.json()["detail"]


def test_empty_file_is_415() -> None:
    response = post(build_client(), "empty.wav", b"")
    assert response.status_code == 415


def test_sniffed_format_beats_extension() -> None:
    # mp3 bytes under a .wav name: accepted, and reported as mp3.
    response = post(build_client(), "en_check_01.wav", FAKE_MP3)
    assert response.status_code == 200
    assert response.json()["format"] == "mp3"



def test_unknown_stem_degrades_to_silence() -> None:
    response = post(build_client(), "never_recorded_this.wav", FAKE_WAV)
    assert response.status_code == 200
    body = response.json()
    assert body["no_speech"] is True
    assert body["transcript"] == ""


def test_hallucinated_text_is_wiped_by_policy() -> None:
    # ambient_hallucination.json carries a real-looking "Thank you." with
    # hallucination-grade segment evidence — the service must wipe it and
    # answer no_speech, not leak the fabrication to the client.
    response = post(build_client(), "ambient_hallucination.wav", FAKE_WAV)
    assert response.status_code == 200
    body = response.json()
    assert body["no_speech"] is True
    assert body["transcript"] == ""