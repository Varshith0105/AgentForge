import os
import subprocess
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import update

from app.api import deps
from app.core.database import get_db
from app.models.models import Project
from app.models.user import User
from app.core.config import settings

router = APIRouter()


class GitHubCloneRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"
    access_token: Optional[str] = None


@router.post("/clone")
async def clone_github_repo(
    payload: GitHubCloneRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Clone a GitHub repository."""
    repo_name = payload.repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    dest = os.path.join("repos", str(current_user.id), repo_name)
    os.makedirs(os.path.dirname(dest), exist_ok=True)

    # Build git URL with optional token auth
    clone_url = payload.repo_url
    if payload.access_token and "github.com" in clone_url:
        clone_url = clone_url.replace("https://", f"https://{payload.access_token}@")

    try:
        result = subprocess.run(
            ["git", "clone", "--depth=1", "-b", payload.branch or "main", clone_url, dest],
            capture_output=True, text=True, timeout=120,
        )
        if result.returncode != 0:
            raise HTTPException(status_code=400, detail=result.stderr or "Clone failed")

        project = Project(
            name=repo_name,
            description=f"Cloned from {payload.repo_url}",
            branch=payload.branch or "main",
            owner_id=current_user.id,
            status="ready",
            is_analyzed=False,
        )
        db.add(project)
        db.flush()
        db.execute(
            update(Project)
            .where(Project.id == project.id)
            .values(
                repo_url=payload.repo_url,
                repo_path=dest,
                branch=payload.branch or "main",
                status="ready",
                is_analyzed=False,
                owner_id=current_user.id,
            )
        )
        db.commit()
        db.refresh(project)

        file_count = sum(1 for _, _, files in os.walk(dest) for _ in files)

        return {
            "message": "Repository cloned successfully",
            "project": {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "repo_url": project.repo_url,
                "repo_path": project.repo_path,
                "branch": project.branch,
                "status": project.status,
                "is_analyzed": project.is_analyzed,
            },
            "files_count": file_count,
            "branch": project.branch,
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Clone timed out")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Git is not installed on the server")


@router.get("/repo-info")
async def get_repo_info(
    repo_url: str,
    access_token: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user),
):
    """Get information about a GitHub repository."""
    import httpx

    # Extract owner/repo from URL
    parts = repo_url.rstrip("/").split("/")
    if len(parts) < 2:
        raise HTTPException(status_code=400, detail="Invalid GitHub URL")

    owner, repo = parts[-2], parts[-1].replace(".git", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if access_token:
        headers["Authorization"] = f"token {access_token}"
    elif settings.GITHUB_CLIENT_SECRET:
        headers["Authorization"] = f"token {settings.GITHUB_CLIENT_SECRET}"

    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
        if resp.status_code == 404:
            raise HTTPException(status_code=404, detail="Repository not found")
        data = resp.json()

    return {
        "name": data.get("name"),
        "full_name": data.get("full_name"),
        "description": data.get("description"),
        "language": data.get("language"),
        "stars": data.get("stargazers_count", 0),
        "forks": data.get("forks_count", 0),
        "default_branch": data.get("default_branch", "main"),
        "size": data.get("size", 0),
    }
