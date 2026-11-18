"""
Project Management Schemas
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    """Create new project"""

    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    """Project information"""

    id: str
    name: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    file_count: int = 0


class ProjectUpdate(BaseModel):
    """Update project"""

    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
