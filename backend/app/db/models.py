"""
Database Models

Phase 1: Core tables for projects, files, and transcripts
Following the principle: preserve original, track all changes

Phase 2+: Extended evaluation and benchmarking system
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, Float, Text, DateTime, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Project(Base):
    """Project container for organizing audio files"""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )


class AudioFile(Base):
    """Original audio file metadata - immutable"""

    __tablename__ = "audio_files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(36), nullable=False)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    original_path: Mapped[str] = mapped_column(String(500), nullable=False)

    # Audio metadata
    duration: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sample_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    channels: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    format: Mapped[str] = mapped_column(String(20), nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)

    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ProcessedAudio(Base):
    """Processed audio variants (noise reduction, dereverberation, etc.)"""

    __tablename__ = "processed_audio"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    original_file_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Processing information
    process_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'noise_reduction', 'dereverberation', etc.
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Output file
    processed_path: Mapped[str] = mapped_column(String(500), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Transcript(Base):
    """Transcription result - stores original AI output"""

    __tablename__ = "transcripts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    audio_file_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Model information
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    language: Mapped[str] = mapped_column(String(10), nullable=False)

    # Processing options
    diarization_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    enhancement_enabled: Mapped[bool] = mapped_column(Boolean, default=False)

    # Timing
    processing_time: Mapped[float] = mapped_column(Float, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class TranscriptSegment(Base):
    """Individual transcript segment with timing and speaker info"""

    __tablename__ = "transcript_segments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    transcript_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Timing
    start_time: Mapped[float] = mapped_column(Float, nullable=False)
    end_time: Mapped[float] = mapped_column(Float, nullable=False)

    # Original AI output (immutable)
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speaker: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # User-edited version (if modified)
    edited_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False)

    # Segment order
    segment_index: Mapped[int] = mapped_column(Integer, nullable=False)


class TranscriptEdit(Base):
    """Edit history for transcript segments - full audit trail"""

    __tablename__ = "transcript_edits"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    segment_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Edit details
    original_text: Mapped[str] = mapped_column(Text, nullable=False)
    edited_text: Mapped[str] = mapped_column(Text, nullable=False)
    edit_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'text', 'speaker', 'timing'

    # Audit
    edited_by: Mapped[str] = mapped_column(String(100), default="user")
    edited_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class AudioQualityAnalysis(Base):
    """
    Audio Quality Analysis Results

    음성 파일의 음향적 특성 및 품질 분석 결과 저장
    각 파일당 하나의 분석 결과 (1:1 관계)
    """

    __tablename__ = "audio_quality_analysis"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    audio_file_id: Mapped[str] = mapped_column(String(36), nullable=False, unique=True)

    # Basic Audio Metadata
    duration: Mapped[float] = mapped_column(Float, nullable=False)
    sample_rate: Mapped[int] = mapped_column(Integer, nullable=False)
    channels: Mapped[int] = mapped_column(Integer, nullable=False)

    # SNR Analysis
    snr_db: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Frequency Analysis
    low_freq_energy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    mid_freq_energy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    high_freq_energy: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spectral_centroid: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spectral_rolloff: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    spectral_bandwidth: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Clipping / Distortion
    clipping_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    clipping_ratio: Mapped[float] = mapped_column(Float, default=0.0)

    # Energy Metrics
    rms_energy: Mapped[float] = mapped_column(Float, nullable=False)
    zero_crossing_rate: Mapped[float] = mapped_column(Float, nullable=False)

    # VAD Analysis
    speech_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    speech_segments_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Reverberation
    reverberation_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 'none', 'low', 'medium', 'high'
    reverberation_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Overlapping Speech
    overlapping_speech_detected: Mapped[bool] = mapped_column(Boolean, default=False)
    overlapping_speech_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Quality Assessment
    quality_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0-100
    quality_issues: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # List of issues as JSON
    noise_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 'low', 'medium', 'high', 'very_high'
    speech_quality: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 'excellent', 'good', 'fair', 'poor'

    # Analysis Metadata
    analyzed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    analysis_version: Mapped[str] = mapped_column(
        String(20), default="1.0.0"
    )  # For tracking analysis algorithm versions


# ============================================================================
# Evaluation & Benchmarking System (Phase 2+)
# ============================================================================


class EvaluationDataset(Base):
    """
    Ground Truth dataset for evaluation

    사용자가 수동으로 검수한 정답 데이터
    """

    __tablename__ = "evaluation_datasets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audio file reference
    audio_file_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Ground truth transcription (human-verified)
    ground_truth_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Ground truth diarization (if available)
    ground_truth_diarization: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"segments": [{"start": 0.0, "end": 3.5, "speaker": "A"}]}

    # Audio quality metadata
    audio_quality: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'clean', 'noisy', 'reverberant', 'very_noisy'
    noise_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 'low', 'medium', 'high'
    reverb_level: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # 'none', 'low', 'medium', 'high'

    # Additional context
    num_speakers: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    language: Mapped[str] = mapped_column(String(10), default="ko")
    tags: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # ["interview", "meeting", "phone"]

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    verified_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)


class ExperimentConfig(Base):
    """
    실험 조건 설정

    동일 오디오에 대해 여러 전처리/모델 조합을 테스트하기 위한 실험 구성
    """

    __tablename__ = "experiment_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Audio preprocessing config
    preprocessing: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"noise_reduction": true, "dereverberation": true, "params": {...}}

    # ASR model config
    asr_model: Mapped[str] = mapped_column(String(100), nullable=False)
    asr_version: Mapped[str] = mapped_column(String(50), nullable=False)
    asr_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # Diarization model config (if enabled)
    diarization_enabled: Mapped[bool] = mapped_column(Boolean, default=False)
    diarization_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    diarization_params: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class Evaluation(Base):
    """
    평가 결과 (확장됨)

    특정 실험 조건에서 특정 데이터셋에 대한 평가 결과
    """

    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Reference to experiment and dataset
    experiment_config_id: Mapped[str] = mapped_column(String(36), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False)
    transcript_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # ASR Metrics
    cer: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Character Error Rate
    wer: Mapped[Optional[float]] = mapped_column(Float, nullable=True)  # Word Error Rate

    # Detailed error breakdown
    substitutions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    deletions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    insertions: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Diarization Metrics (if applicable)
    der: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Diarization Error Rate
    jer: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Jaccard Error Rate

    # Diarization error breakdown
    miss_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Missed speech
    false_alarm_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # False detection
    confusion_rate: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Speaker confusion

    # Performance Metrics
    rtf: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Real-Time Factor
    processing_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Total processing time (seconds)
    model_load_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Model loading time
    first_token_time: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Time to first result

    # System Resource Usage
    peak_memory_mb: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Peak RAM usage
    avg_memory_mb: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Average RAM usage
    cpu_usage_percent: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Average CPU %
    gpu_usage_percent: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Average GPU %

    # Additional metadata
    audio_duration: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Audio length in seconds
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_log: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # If evaluation failed

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)


class ModelBenchmark(Base):
    """
    모델별 종합 벤치마크 결과

    여러 평가 결과를 집계한 모델의 전체 성능 요약
    """

    __tablename__ = "model_benchmarks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)

    # Model information
    model_name: Mapped[str] = mapped_column(String(100), nullable=False)
    model_version: Mapped[str] = mapped_column(String(50), nullable=False)
    model_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # 'asr', 'diarization', 'enhancement'

    # Aggregated metrics (average across all evaluations)
    num_evaluations: Mapped[int] = mapped_column(
        Integer, nullable=False
    )  # Number of evaluations
    avg_cer: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_wer: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_der: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_rtf: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    avg_peak_memory_mb: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Performance by audio quality
    metrics_by_quality: Mapped[Optional[dict]] = mapped_column(
        JSON, nullable=True
    )  # {"clean": {"cer": 5.2}, "noisy": {"cer": 18.5}}

    # Hardware info
    hardware: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # 'M4 Mac 16GB', etc.

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now
    )
