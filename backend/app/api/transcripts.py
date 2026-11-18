"""
Transcript Management API

Handles transcript editing, history tracking, and export
"""

from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from app.schemas.transcript import (
    TranscriptUpdate,
    TranscriptHistory,
    TranscriptExport,
)

router = APIRouter()


@router.get("/{file_id}/history", response_model=list[TranscriptHistory])
async def get_transcript_history(file_id: str):
    """Get edit history for a transcript"""
    return [
        TranscriptHistory(
            timestamp=datetime.now(),
            segment_index=1,
            original_text="안녕하세요 이것은 테스트 음성입니다",
            edited_text="안녕하세요, 이것은 테스트 음성입니다.",
            editor="user",
        )
    ]


@router.patch("/{file_id}")
async def update_transcript(file_id: str, update: TranscriptUpdate):
    """Update transcript segments or metadata"""
    return {
        "status": "updated",
        "file_id": file_id,
        "segments_updated": len(update.segments) if update.segments else 0,
    }


@router.post("/{file_id}/export")
async def export_transcript(file_id: str, export_config: TranscriptExport):
    """
    Export transcript in specified format

    Phase 1: Returns simple text format
    """
    if export_config.format == "txt":
        content = """[SPEAKER_00] 0.0 - 3.5
안녕하세요 이것은 테스트 음성입니다

[SPEAKER_00] 3.5 - 7.2
음성 인식 시스템이 정상적으로 작동하고 있습니다

[SPEAKER_01] 8.0 - 11.5
저음질 환경에서도 견고한 인식을 목표로 합니다
"""
        return PlainTextResponse(content=content)

    return {"status": "exported", "format": export_config.format, "file_id": file_id}
