

from __future__ import annotations

from services.transcription_port import Segment


NO_SPEECH_PROB_THRESHOLD = 0.90   
AVG_LOGPROB_THRESHOLD = -1.50    
AVG_LOGPROB_HARD_FLOOR = -2.50   


def segment_is_junk(segment: Segment) -> bool:
   
    if segment.avg_logprob <= AVG_LOGPROB_HARD_FLOOR:
        return True
    return (
        segment.no_speech_prob >= NO_SPEECH_PROB_THRESHOLD
        and segment.avg_logprob <= AVG_LOGPROB_THRESHOLD
    )


def is_no_speech(segments: tuple[Segment, ...], *, vad_filtered_all: bool) -> bool:
   
    if vad_filtered_all or not segments:
        return True
    return all(segment_is_junk(s) for s in segments)