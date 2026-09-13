

from __future__ import annotations

_SIMPLE_MAGICS: tuple[tuple[str, bytes], ...] = (
    ("ogg", b"OggS"),
    ("flac", b"fLaC"),
    ("mp3", b"ID3"),
    ("webm", b"\x1a\x45\xdf\xa3"),  # EBML header (webm/mkv audio)
)


def sniff_audio_format(data: bytes) -> str | None:
    
    if not data:
        return None
    for name, magic in _SIMPLE_MAGICS:
        if data.startswith(magic):
            return name
    if data.startswith(b"RIFF") and data[8:12] == b"WAVE":
        return "wav"
    if len(data) >= 12 and data[4:8] == b"ftyp":
        return "m4a"  # ISO-BMFF audio (m4a/m4b/mp4)
    if len(data) >= 2 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0:
        return "mp3"  # raw MPEG frame sync without an ID3 tag
    return None