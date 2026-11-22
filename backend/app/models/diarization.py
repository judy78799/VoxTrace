"""
Speaker Diarization Model Interface

Phase 1: Interface only
Future: pyannote.audio integration
"""

from typing import Optional
from dataclasses import dataclass

from app.models.base import BaseModel, ModelInfo


@dataclass
class SpeakerSegment:
    """Speaker segment with timing"""

    start: float
    end: float
    speaker: str  # 'SPEAKER_00', 'SPEAKER_01', etc.


@dataclass
class DiarizationResult:
    """Complete diarization result"""

    segments: list[SpeakerSegment]
    num_speakers: int
    processing_time: float


class DiarizationModel(BaseModel):
    """
    Speaker Diarization abstraction

    Planned: pyannote.audio
    Note: Runs in parallel with ASR, merged by timestamp alignment
    """

    def __init__(self):
        super().__init__()

    async def load(self) -> None:
        """Load diarization model - Phase 1: Not implemented"""
        # Future: Load pyannote.audio
        self._loaded = False

    async def unload(self) -> None:
        """Unload model"""
        self._loaded = False
        self._model = None

    async def diarize(self, audio_path: str) -> DiarizationResult:
        """
        Perform speaker diarization

        Phase 1: Returns dummy result
        """
        return DiarizationResult(
            segments=[
                SpeakerSegment(start=0.0, end=7.0, speaker="SPEAKER_00"),
                SpeakerSegment(start=7.5, end=12.0, speaker="SPEAKER_01"),
            ],
            num_speakers=2,
            processing_time=1.2,
        )

    def get_info(self) -> ModelInfo:
        """Get model information"""
        return ModelInfo(
            name="pyannote-diarization",
            version="phase1-dummy",
            loaded=self._loaded,
            device="not_loaded",
        )
