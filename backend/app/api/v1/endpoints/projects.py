import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.models import Project, Analysis
from app.services.platform_engine import repository_files, repository_stats
from typing import cast

router = APIRouter()


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    repo_url: Optional[str] = None
    branch: Optional[str] = "main"
    language: Optional[str] = None
    framework: Optional[str] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str]
    repo_url: Optional[str]
    branch: str
    language: Optional[str]
    framework: Optional[str]
    status: str
    is_analyzed: bool
    created_at: datetime


class ProjectFileResponse(BaseModel):
    project_id: str
    files: list[dict]
    stats: dict


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    projects = db.query(Project).filter(Project.owner_id == current_user.id).order_by(Project.created_at.desc()).all()
    return projects


@router.post("", response_model=ProjectResponse, status_code=201)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    project = Project(
        id=str(uuid.uuid4()),
        name=payload.name,
        description=payload.description,
        repo_url=payload.repo_url,
        branch=payload.branch or "main",
        language=payload.language,
        framework=payload.framework,
        owner_id=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/recent-activity")
def get_recent_activity_top(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    projects = db.query(Project).filter(
        Project.owner_id == current_user.id
    ).order_by(Project.updated_at.desc()).limit(10).all()
    return {"activities": [{"project_id": p.id, "name": p.name, "updated_at": p.updated_at} for p in projects]}


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}")
def delete_project(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(project)
    db.commit()
    return {"message": "Project deleted"}


@router.get("/{project_id}/summary")
def get_project_summary(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    analyses = db.query(Analysis).filter(Analysis.project_id == project_id).order_by(Analysis.created_at.desc()).all()
    return {
        "project": {
            "id": project.id,
            "name": project.name,
            "repo_url": project.repo_url,
            "branch": project.branch,
            "language": project.language,
            "status": project.status,
        },
        "analyses_count": len(analyses),
        "last_analysis": analyses[0].created_at.isoformat() if analyses else None,
    }





@router.get("/{project_id}/files", response_model=ProjectFileResponse)
def get_project_files(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo_path = str(getattr(project, "repo_path", "") or "")
    files = repository_files(repo_path) if repo_path else []
    stats = repository_stats(repo_path) if repo_path else repository_stats("__missing__")
    return {"project_id": project.id, "files": files, "stats": stats}
