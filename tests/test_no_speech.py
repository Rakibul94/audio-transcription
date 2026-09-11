

from __future__ import annotations

from services.no_speech import is_no_speech
from services.transcription_port import Segment


def seg(prob: float, logprob: float) -> Segment:
    return Segment(text="x", no_speech_prob=prob, avg_logprob=logprob)


def test_vad_verdict_ends_the_argument() -> None:
    assert is_no_speech((), vad_filtered_all=True) is True


def test_hallucination_needs_both_signals() -> None:
    assert is_no_speech((seg(0.95, -0.3),), vad_filtered_all=False) is False  # unsure framing, real speech
    assert is_no_speech((seg(0.2, -1.2),), vad_filtered_all=False) is False   # hard audio above the floor
    assert is_no_speech((seg(0.93, -1.8),), vad_filtered_all=False) is True   # both signals
    assert is_no_speech((seg(0.6, -1.0),), vad_filtered_all=False) is False   # boundaries are strict

def test_music_hallucination_hits_hard_floor() -> None:
    # observed on bangla_alien_podcast: music scores logprob -2.70 with no_speech 0.08
    assert is_no_speech((seg(0.08, -2.70),), vad_filtered_all=False) is True
    assert is_no_speech((seg(0.2, -1.5),), vad_filtered_all=False) is False    # exactly at floor: still speech

def test_one_confident_segment_survives() -> None:
    mixed = (seg(0.08, -2.70), seg(0.07, -0.40))   # music junk + real speech
    assert is_no_speech(mixed, vad_filtered_all=False) is False