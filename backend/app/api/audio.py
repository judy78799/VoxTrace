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
)
from app.utils.audio import extract_metadata_ffmpeg, validate_audio_file
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


# Global ASR model instance (lazy loading)
from app.models.asr import ASRModel

asr_model = ASRModel(model_name="medium")


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

    # 2. ASR 모델로 전사 수행
    try:
        asr_result = await asr_model.transcribe(
            audio_path=audio_file.original_path,
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

    # 4. 응답 반환
    response_segments = [
        TranscriptionSegment(
            start=seg.start,
            end=seg.end,
            text=seg.text,
            speaker=None,
            confidence=seg.confidence,
        )
        for seg in asr_result.segments
    ]

    return TranscriptionResult(
        file_id=audio_file.id,
        segments=response_segments,
        language=asr_result.language,
        processing_time=asr_result.processing_time,
        model_version=f"mlx-whisper-{asr_model.model_name}",
        created_at=transcript.created_at,
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
