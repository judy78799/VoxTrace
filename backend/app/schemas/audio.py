"""
Audio Processing Schemas

Pydantic models for audio upload, processing, and results
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class AudioUploadResponse(BaseModel):
    """Response after uploading audio"""

    file_id: str = Field(..., description="Unique file identifier")
    filename: str
    duration: Optional[float] = Field(None, description="Duration in seconds")
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    format: str
    size_bytes: int
    uploaded_at: datetime


class TranscriptionRequest(BaseModel):
    """Request to transcribe audio"""

    file_id: str
    enable_vad: bool = True  # Voice Activity Detection (무음 제거)
    enable_diarization: bool = True
    enable_enhancement: bool = False
    language: str = "ko"


class TranscriptionSegment(BaseModel):
    """Single transcription segment"""

    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class VADAnalysis(BaseModel):
    """VAD 분석 정보"""

    enabled: bool
    original_duration: Optional[float] = None
    processed_duration: Optional[float] = None
    silence_removed: Optional[float] = None
    speech_segments_count: Optional[int] = None


class AudioQualityMetrics(BaseModel):
    """오디오 품질 지표"""

    sample_rate: int
    channels: int
    duration: float
    file_size_mb: float


class TranscriptionResult(BaseModel):
    """Complete transcription result"""

    file_id: str
    segments: list[TranscriptionSegment]
    language: str
    processing_time: float
    model_version: str
    created_at: datetime

    # 분석 정보
    vad_analysis: Optional[VADAnalysis] = None
    audio_quality: Optional[AudioQualityMetrics] = None
    rtf: Optional[float] = Field(None, description="Real-Time Factor (processing_time / audio_duration)")
