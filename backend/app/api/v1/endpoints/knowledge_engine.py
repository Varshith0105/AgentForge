from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import cast
from sqlalchemy import update

from app.api import deps
from app.core.database import get_db
from app.models.models import Project
from app.models.user import User
from app.services.platform_engine import build_knowledge_graph, repository_memory, search_repository

router = APIRouter()


class KnowledgeSearchRequest(BaseModel):
    query: str
    project_id: Optional[str] = None
    limit: Optional[int] = 10


@router.get("/graph/{project_id}")
def get_knowledge_graph(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Return knowledge graph data for a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_repo_path = str(getattr(project, "repo_path", "") or "")
    if not project_repo_path:
        return {
            "project_id": project_id,
            "nodes": [],
            "edges": [],
            "stats": {
                "total_files": 0,
                "total_functions": 0,
                "total_classes": 0,
                "total_imports": 0,
            },
        }

    graph = build_knowledge_graph(project_repo_path)
    return {"project_id": project_id, **graph}


@router.post("/search")
def search_knowledge(
    payload: KnowledgeSearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Search the knowledge base."""
    if not payload.project_id:
        return {"query": payload.query, "results": [], "total": 0}

    project = db.query(Project).filter(Project.id == payload.project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo_path = str(getattr(project, "repo_path", "") or "")
    results = search_repository(repo_path, payload.query, limit=payload.limit or 10) if repo_path else []
    return {"query": payload.query, "results": results, "total": len(results)}


@router.get("/memory/{project_id}")
def get_project_memory(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Get repository memory for a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    project_repo_path = str(getattr(project, "repo_path", "") or "")
    if not project_repo_path:
        return {"project_id": project_id, "memories": [], "context_summary": "Repository not indexed yet.", "vector_count": 0}

    memory = repository_memory(project_repo_path)
    return {"project_id": project_id, **memory}


@router.post("/index/{project_id}")
async def index_repository(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Trigger knowledge graph indexing for a project."""
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == current_user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project_repo_path = str(getattr(project, "repo_path", "") or "")
    if not project_repo_path:
        raise HTTPException(status_code=400, detail="Project does not have a repository path")

    graph = build_knowledge_graph(project_repo_path)
    db.execute(
        update(Project)
        .where(Project.id == project_id, Project.owner_id == current_user.id)
        .values(status="indexed", is_analyzed=True)
    )
    db.commit()
    return {
        "message": "Indexing completed",
        "project_id": project_id,
        "status": "completed",
        "stats": graph["stats"],
    }
