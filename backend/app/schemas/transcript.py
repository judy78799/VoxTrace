"""
Transcript Management Schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class TranscriptSegmentUpdate(BaseModel):
    """Update a transcript segment"""

    text: str
    speaker: Optional[str] = None


class TranscriptUpdate(BaseModel):
    """Update transcript metadata or segments"""

    segments: Optional[list[TranscriptSegmentUpdate]] = None
    notes: Optional[str] = None


class TranscriptHistory(BaseModel):
    """Transcript edit history entry"""

    timestamp: datetime
    segment_index: int
    original_text: str
    edited_text: str
    editor: str = "user"


class TranscriptExport(BaseModel):
    """Export format options"""

    format: str = Field(..., pattern="^(txt|srt|vtt|json)$")
    include_timestamps: bool = True
    include_speakers: bool = True
    include_confidence: bool = False
