
from __future__ import annotations

from services.audio_format import sniff_audio_format

WAV = b"RIFF" + b"\x00" * 4 + b"WAVE" + b"\x00" * 32
MP3_ID3 = b"ID3\x04\x00" + b"\x00" * 32
MP3_SYNC = b"\xff\xfb\x90\x00" + b"\x00" * 32
OGG = b"OggS" + b"\x00" * 32
FLAC = b"fLaC" + b"\x00" * 32
M4A = b"\x00\x00\x00\x20ftypM4A " + b"\x00" * 32
WEBM = b"\x1a\x45\xdf\xa3" + b"\x00" * 32


def test_sniffs_each_supported_format() -> None:
    assert sniff_audio_format(WAV) == "wav"
    assert sniff_audio_format(MP3_ID3) == "mp3"
    assert sniff_audio_format(MP3_SYNC) == "mp3"
    assert sniff_audio_format(OGG) == "ogg"
    assert sniff_audio_format(FLAC) == "flac"
    assert sniff_audio_format(M4A) == "m4a"
    assert sniff_audio_format(WEBM) == "webm"


def test_riff_but_not_wave_is_not_wav() -> None:
    avi = b"RIFF" + b"\x00" * 4 + b"AVI " + b"\x00" * 32
    assert sniff_audio_format(avi) is None


def test_empty_and_garbage_sniff_none() -> None:
    assert sniff_audio_format(b"") is None
    assert sniff_audio_format(b"not audio at all") is None