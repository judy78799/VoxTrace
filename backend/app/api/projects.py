"""
Project Management API

Handles project creation, listing, and management
"""

from datetime import datetime

from fastapi import APIRouter

from app.schemas.project import ProjectCreate, ProjectResponse, ProjectUpdate

router = APIRouter()


@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate):
    """Create a new project"""
    return ProjectResponse(
        id="proj-dummy-001",
        name=project.name,
        description=project.description,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        file_count=0,
    )


@router.get("/", response_model=list[ProjectResponse])
async def list_projects():
    """List all projects"""
    return [
        ProjectResponse(
            id="proj-demo-001",
            name="Demo Project",
            description="Sample project for testing",
            created_at=datetime.now(),
            updated_at=datetime.now(),
            file_count=3,
        )
    ]


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str):
    """Get project details"""
    return ProjectResponse(
        id=project_id,
        name="Sample Project",
        description="This is a dummy project",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        file_count=5,
    )


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, update: ProjectUpdate):
    """Update project information"""
    return ProjectResponse(
        id=project_id,
        name=update.name or "Updated Project",
        description=update.description,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        file_count=5,
    )


@router.delete("/{project_id}")
async def delete_project(project_id: str):
    """Delete a project"""
    return {"status": "deleted", "project_id": project_id}
