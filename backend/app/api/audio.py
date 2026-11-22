"""
Audio Upload and Processing API

Handles audio file uploads, preprocessing, and transcription requests
"""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Annotated, Optional

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db.models import AudioFile, Project
from app.schemas.audio import (
    AudioUploadResponse,
    TranscriptionRequest,
    TranscriptionResult,
    TranscriptionSegment,
    QualityFlag,
    VADAnalysis,
    AudioQualityMetrics,
    SignalAnalysis,
    FrequencyAnalysis,
)
from app.utils.audio import extract_metadata_ffmpeg, validate_audio_file
from app.utils.post_processing import filter_suspicious_segments
from app.core.config import settings

router = APIRouter()


async def get_or_create_default_project(db: AsyncSession) -> str:
    """기본 프로젝트 가져오기 또는 생성"""
    # Check if default project exists
    result = await db.execute(
        select(Project).where(Project.name == "Default Project")
    )
    project = result.scalar_one_or_none()

    if not project:
        # Create default project
        project = Project(
            id=str(uuid.uuid4()),
            name="Default Project",
            description="자동 생성된 기본 프로젝트",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        db.add(project)
        await db.commit()
        await db.refresh(project)

    return project.id


@router.post("/upload", response_model=AudioUploadResponse)
async def upload_audio(
    file: Annotated[UploadFile, File(description="Audio file to upload")],
    project_id: Annotated[Optional[str], Form(description="Project ID (optional)")] = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Upload an audio file for processing

    Phase 2: 실제 파일 저장 및 메타데이터 추출
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # 파일 크기 체크
    file_content = await file.read()
    file_size = len(file_content)

    if file_size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large: {file_size / 1024 / 1024:.1f}MB "
                   f"(max: {settings.MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB)"
        )

    # 고유 ID 생성
    file_id = str(uuid.uuid4())

    # 프로젝트 ID 확인 또는 기본 프로젝트 사용
    if not project_id:
        project_id = await get_or_create_default_project(db)
    else:
        # 프로젝트 존재 여부 확인
        result = await db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(status_code=404, detail=f"Project not found: {project_id}")

    # 파일 저장 경로 생성
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)

    # 안전한 파일명 생성 (UUID_원본파일명)
    safe_filename = f"{file_id}_{file.filename}"
    file_path = upload_dir / safe_filename

    # 파일 저장
    try:
        with open(file_path, "wb") as f:
            f.write(file_content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save file: {str(e)}"
        )

    # 메타데이터 추출
    try:
        metadata = extract_metadata_ffmpeg(str(file_path))
    except Exception as e:
        # 파일 저장은 성공했지만 메타데이터 추출 실패
        file_path.unlink()  # 파일 삭제
        raise HTTPException(
            status_code=400,
            detail=f"Invalid audio file: {str(e)}"
        )

    # 데이터베이스에 기록
    audio_file = AudioFile(
        id=file_id,
        project_id=project_id,
        filename=file.filename,
        original_path=str(file_path),
        duration=metadata['duration'],
        sample_rate=metadata['sample_rate'],
        channels=metadata['channels'],
        format=metadata['format'],
        size_bytes=file_size,
        uploaded_at=datetime.now(),
    )

    db.add(audio_file)
    await db.commit()
    await db.refresh(audio_file)

    return AudioUploadResponse(
        file_id=audio_file.id,
        filename=audio_file.filename,
        duration=audio_file.duration,
        sample_rate=audio_file.sample_rate,
        channels=audio_file.channels,
        format=audio_file.format,
        size_bytes=audio_file.size_bytes,
        uploaded_at=audio_file.uploaded_at,
    )


# Global model instances (lazy loading)
from app.models.asr import ASRModel
from app.models.vad import VADModel
from app.models.audio_analysis import AudioAnalysisModel
from app.models.enhancement import EnhancementModel

asr_model = ASRModel(model_name="medium")
vad_model = VADModel()
audio_analysis_model = AudioAnalysisModel()
enhancement_model = EnhancementModel()


@router.post("/transcribe", response_model=TranscriptionResult)
async def transcribe_audio(
    request: TranscriptionRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Transcribe uploaded audio file using MLX Whisper

    Phase 3: 실제 음성 인식 수행
    """
    # 1. 오디오 파일 조회
    result = await db.execute(
        select(AudioFile).where(AudioFile.id == request.file_id)
    )
    audio_file = result.scalar_one_or_none()

    if not audio_file:
        raise HTTPException(
            status_code=404,
            detail=f"Audio file not found: {request.file_id}"
        )

    # 2. 오디오 신호 분석 (원본 파일)
    signal_analysis_result = None
    try:
        print(f"🔬 Analyzing audio signal quality...")
        analysis_result = await audio_analysis_model.analyze(
            audio_path=audio_file.original_path,
            generate_spectrogram=True,
        )

        # 스키마로 변환
        signal_analysis_result = SignalAnalysis(
            snr_db=analysis_result.snr_db,
            frequency_analysis=FrequencyAnalysis(
                low_freq_energy=analysis_result.frequency_analysis.low_freq_energy,
                mid_freq_energy=analysis_result.frequency_analysis.mid_freq_energy,
                high_freq_energy=analysis_result.frequency_analysis.high_freq_energy,
                spectral_centroid=analysis_result.frequency_analysis.spectral_centroid,
                spectral_rolloff=analysis_result.frequency_analysis.spectral_rolloff,
                spectral_bandwidth=analysis_result.frequency_analysis.spectral_bandwidth,
            ) if analysis_result.frequency_analysis else None,
            clipping_detected=analysis_result.clipping_detected,
            clipping_percentage=analysis_result.clipping_percentage,
            rms_energy=analysis_result.rms_energy,
            zero_crossing_rate=analysis_result.zero_crossing_rate,
            spectrogram_base64=analysis_result.spectrogram_base64,
            quality_score=analysis_result.quality_score,
            quality_issues=analysis_result.quality_issues,
        )
        print(f"✅ Signal analysis complete: Quality score = {analysis_result.quality_score:.1f}/100")
    except Exception as e:
        print(f"⚠️  Signal analysis failed: {e}")
        # 분석 실패해도 전사는 계속 진행

    # 3. Speech Enhancement (옵션)
    audio_path_for_processing = audio_file.original_path
    enhancement_result = None

    if request.enable_enhancement:
        try:
            print(f"🎵 Applying Speech Enhancement (noisereduce)...")
            enhancement_result = await enhancement_model.enhance_audio(
                audio_path=audio_file.original_path,
                output_path=None,  # 자동 생성 (_enhanced suffix)
            )
            # Enhancement 처리된 파일 사용
            audio_path_for_processing = enhancement_result.enhanced_path
            print(f"✅ Enhancement complete: {enhancement_result.processing_time:.2f}s processing time")
        except Exception as e:
            print(f"⚠️  Enhancement failed, using original audio: {e}")
            # Enhancement 실패 시 원본 사용

    # 4. VAD 전처리 (옵션)
    audio_path_for_asr = audio_path_for_processing
    vad_result = None

    if request.enable_vad:
        try:
            print(f"🎙️  Applying VAD preprocessing...")
            vad_result = await vad_model.process_audio(
                audio_path=audio_path_for_processing,  # Enhancement 적용된 오디오 사용
                output_path=None,  # 자동 생성 (_vad suffix)
            )
            # VAD 처리된 파일 사용
            audio_path_for_asr = str(Path(audio_path_for_processing).parent /
                                    f"{Path(audio_path_for_processing).stem}_vad{Path(audio_path_for_processing).suffix}")
            print(f"✅ VAD complete: {vad_result.silence_removed:.2f}s silence removed")
        except Exception as e:
            print(f"⚠️  VAD failed, using previous audio: {e}")
            # VAD 실패 시 이전 단계 오디오 사용

    # 5. ASR 모델로 전사 수행
    try:
        asr_result = await asr_model.transcribe(
            audio_path=audio_path_for_asr,
            language=request.language,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

    # 3. 데이터베이스에 저장
    from app.db.models import Transcript, TranscriptSegment as DBTranscriptSegment

    transcript = Transcript(
        id=str(uuid.uuid4()),
        audio_file_id=audio_file.id,
        model_name="mlx-whisper",
        model_version=asr_model.model_name,
        language=request.language,
        diarization_enabled=request.enable_diarization,
        enhancement_enabled=request.enable_enhancement,
        processing_time=asr_result.processing_time,
        created_at=datetime.now(),
    )
    db.add(transcript)

    # 세그먼트 저장
    for idx, seg in enumerate(asr_result.segments):
        db_segment = DBTranscriptSegment(
            id=str(uuid.uuid4()),
            transcript_id=transcript.id,
            start_time=seg.start,
            end_time=seg.end,
            original_text=seg.text,
            confidence=seg.confidence,
            speaker=None,  # Diarization Phase 4에서 구현
            edited_text=None,
            is_edited=False,
            segment_index=idx,
        )
        db.add(db_segment)

    await db.commit()
    await db.refresh(transcript)

    # 4. Post-processing: 품질 플래그 및 의심 세그먼트 필터링
    print(f"\n🔍 Running post-processing quality analysis...")

    # 세그먼트를 딕셔너리 형태로 변환
    segments_dict = [
        {
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "confidence": seg.confidence if seg.confidence is not None else 1.0,
        }
        for seg in asr_result.segments
    ]

    # 품질 분석 및 필터링
    processed_segments = filter_suspicious_segments(
        segments_dict,
        auto_filter=request.enable_auto_filter
    )

    # 통계 출력
    suspicious_count = sum(1 for seg in processed_segments if seg["is_suspicious"])
    filtered_count = sum(1 for seg in processed_segments if seg["is_filtered"])
    print(f"   Total segments: {len(processed_segments)}")
    print(f"   Suspicious segments: {suspicious_count}")
    if request.enable_auto_filter:
        print(f"   Auto-filtered: {filtered_count}")
    print(f"✅ Post-processing complete\n")

    # 5. 응답 반환
    response_segments = [
        TranscriptionSegment(
            start=seg["start"],
            end=seg["end"],
            text=seg["text"],
            speaker=None,
            confidence=seg["confidence"],
            quality_flags=[
                QualityFlag(
                    type=flag["type"],
                    severity=flag["severity"],
                    reason=flag["reason"]
                )
                for flag in seg["quality_flags"]
            ],
            is_suspicious=seg["is_suspicious"],
            is_filtered=seg["is_filtered"],
        )
        for seg in processed_segments
    ]

    # VAD 분석 정보
    vad_analysis = None
    if vad_result:
        vad_analysis = VADAnalysis(
            enabled=True,
            original_duration=vad_result.original_duration,
            processed_duration=vad_result.processed_duration,
            silence_removed=vad_result.silence_removed,
            speech_segments_count=len(vad_result.segments),
        )
    else:
        vad_analysis = VADAnalysis(enabled=False)

    # 오디오 품질 지표
    audio_quality = AudioQualityMetrics(
        sample_rate=audio_file.sample_rate or 0,
        channels=audio_file.channels or 0,
        duration=audio_file.duration or 0.0,
        file_size_mb=audio_file.size_bytes / 1024 / 1024,
    )

    # RTF (Real-Time Factor) 계산
    rtf = asr_result.processing_time / audio_file.duration if audio_file.duration else None

    return TranscriptionResult(
        file_id=audio_file.id,
        segments=response_segments,
        language=asr_result.language,
        processing_time=asr_result.processing_time,
        model_version=f"mlx-whisper-{asr_model.model_name}",
        created_at=transcript.created_at,
        vad_analysis=vad_analysis,
        audio_quality=audio_quality,
        signal_analysis=signal_analysis_result,
        rtf=rtf,
    )


@router.get("/file/{file_id}")
async def get_audio_info(file_id: str):
    """Get audio file metadata"""
    return {
        "file_id": file_id,
        "status": "ready",
        "metadata": {
            "duration": 120.5,
            "sample_rate": 16000,
            "channels": 1,
        },
    }
