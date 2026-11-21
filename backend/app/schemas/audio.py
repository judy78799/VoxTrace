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


class FrequencyAnalysis(BaseModel):
    """주파수 분석 결과"""

    low_freq_energy: float = Field(..., description="저주파 에너지 (0-300Hz)")
    mid_freq_energy: float = Field(..., description="중간 주파수 에너지 (300-3000Hz)")
    high_freq_energy: float = Field(..., description="고주파 에너지 (3000Hz+)")
    spectral_centroid: float = Field(..., description="스펙트럼 중심 (Hz)")
    spectral_rolloff: float = Field(..., description="스펙트럼 롤오프 (Hz)")
    spectral_bandwidth: float = Field(..., description="스펙트럼 대역폭 (Hz)")


class SignalAnalysis(BaseModel):
    """오디오 신호 분석 결과"""

    # SNR
    snr_db: Optional[float] = Field(None, description="Signal-to-Noise Ratio (dB)")

    # 주파수 분석
    frequency_analysis: Optional[FrequencyAnalysis] = None

    # 클리핑/왜곡
    clipping_detected: bool = False
    clipping_percentage: float = 0.0

    # 에너지
    rms_energy: float = 0.0
    zero_crossing_rate: float = 0.0

    # 스펙트로그램 (Base64 PNG)
    spectrogram_base64: Optional[str] = None

    # 품질 평가
    quality_score: float = Field(..., ge=0.0, le=100.0, description="품질 점수 (0-100)")
    quality_issues: list[str] = Field(default_factory=list, description="감지된 품질 문제")


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
    signal_analysis: Optional[SignalAnalysis] = None
    rtf: Optional[float] = Field(None, description="Real-Time Factor (processing_time / audio_duration)")
