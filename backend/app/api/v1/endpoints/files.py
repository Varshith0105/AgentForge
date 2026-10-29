"""
File content API -- read individual files from a project repository.
Security: path is validated to stay within the project repo_path.
"""
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.models.models import Project
from app.models.user import User

router = APIRouter()

MAX_FILE_BYTES = 2 * 1024 * 1024

LANGUAGE_MAP = {
    ".py": "python", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript", ".json": "json",
    ".md": "markdown", ".txt": "plaintext", ".yaml": "yaml",
    ".yml": "yaml", ".html": "html", ".css": "css", ".scss": "scss",
    ".sql": "sql", ".sh": "shell", ".bash": "shell", ".go": "go",
    ".rs": "rust", ".java": "java", ".cpp": "cpp", ".c": "c",
    ".h": "cpp", ".rb": "ruby", ".php": "php", ".swift": "swift",
    ".kt": "kotlin", ".toml": "toml", ".xml": "xml",
    ".env": "plaintext", ".gitignore": "plaintext",
}

SKIP_DIRS = {
    ".git", "node_modules", "dist", "build", ".venv", "venv",
    "__pycache__", ".next", ".turbo", ".mypy_cache", ".pytest_cache",
    "target", ".cargo", ".gradle", ".idea", ".vscode"
}


@router.get("/{project_id}/content")
def get_file_content(
    project_id: str,
    path: str = Query(..., description="Relative file path within the repository"),
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Read the content of a specific file from a project repository."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo_path_str = str(getattr(project, "repo_path", "") or "")
    if not repo_path_str:
        raise HTTPException(status_code=400, detail="Project has no repository path. Clone a repository first.")

    repo_root = Path(repo_path_str).resolve()

    try:
        requested = (repo_root / path).resolve()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid file path")

    try:
        requested.relative_to(repo_root)
    except ValueError:
        raise HTTPException(status_code=403, detail="Access denied: path is outside the repository")

    if not requested.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    if not requested.is_file():
        raise HTTPException(status_code=400, detail="Path points to a directory, not a file")

    file_size = requested.stat().st_size
    if file_size > MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({file_size // 1024} KB). Max {MAX_FILE_BYTES // 1024} KB."
        )

    suffix = requested.suffix.lower()
    language = LANGUAGE_MAP.get(suffix, "plaintext")

    try:
        content = requested.read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Could not read file: {exc}")

    return {
        "project_id": project_id,
        "path": path,
        "name": requested.name,
        "language": language,
        "content": content,
        "size": file_size,
        "lines": content.count("\n") + 1,
    }


@router.get("/{project_id}/tree")
def get_file_tree(
    project_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Return a nested file tree for a project repository."""
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    repo_path_str = str(getattr(project, "repo_path", "") or "")
    if not repo_path_str:
        return {"project_id": project_id, "tree": [], "total_files": 0}

    repo_root = Path(repo_path_str)
    if not repo_root.exists():
        return {"project_id": project_id, "tree": [], "total_files": 0}

    def build_tree(directory: Path, root: Path) -> list:
        items = []
        try:
            entries = sorted(directory.iterdir(), key=lambda e: (e.is_file(), e.name.lower()))
        except PermissionError:
            return []
        for entry in entries:
            if entry.name.startswith(".") and entry.name not in {".env", ".gitignore", ".env.example"}:
                continue
            if entry.is_dir() and entry.name in SKIP_DIRS:
                continue
            rel_path = str(entry.relative_to(root)).replace("\\", "/")
            if entry.is_dir():
                children = build_tree(entry, root)
                items.append({"name": entry.name, "path": rel_path, "type": "directory", "children": children})
            else:
                suffix = entry.suffix.lower()
                items.append({
                    "name": entry.name, "path": rel_path, "type": "file",
                    "language": LANGUAGE_MAP.get(suffix, "plaintext"),
                    "size": entry.stat().st_size,
                })
        return items

    tree = build_tree(repo_root, repo_root)
    total = sum(1 for _ in repo_root.rglob("*") if _.is_file())
    return {"project_id": project_id, "tree": tree, "total_files": total}
