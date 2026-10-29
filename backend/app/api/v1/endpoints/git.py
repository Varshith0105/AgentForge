import os
import subprocess
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api import deps
from app.models.user import User
from app.core.config import settings

router = APIRouter()


class GitCommandRequest(BaseModel):
    command: str
    repo_path: Optional[str] = None
    args: Optional[List[str]] = None


class GitCloneRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"
    destination: Optional[str] = None


def _repo_path(path: Optional[str], allow_missing: bool = False) -> Path:
    root = Path(settings.WORKSPACE_ROOT).resolve()
    candidate = (root / (path or ".")).resolve() if not os.path.isabs(path or "") else Path(path).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=403, detail="Repository path is outside the workspace") from exc
    if not allow_missing and not candidate.exists():
        raise HTTPException(status_code=404, detail="Repository path does not exist")
    return candidate


def run_git(args: List[str], cwd: Optional[str] = None) -> dict:
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            timeout=60,
            cwd=cwd or os.getcwd(),
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "success": result.returncode == 0,
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "Git command timed out", "returncode": -1, "success": False}
    except FileNotFoundError:
        return {"stdout": "", "stderr": "Git not found. Install git.", "returncode": -1, "success": False}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "success": False}


@router.post("/clone")
def git_clone(
    payload: GitCloneRequest,
    current_user: User = Depends(deps.get_current_user),
):
    parsed = urlparse(payload.repo_url)
    if parsed.scheme not in {"https", "ssh"} or parsed.hostname not in {"github.com", "www.github.com"}:
        raise HTTPException(status_code=400, detail="Only GitHub HTTPS or SSH URLs are supported")
    name = Path(parsed.path).name.removesuffix(".git")
    if not name:
        raise HTTPException(status_code=400, detail="Repository URL must include a repository name")
    dest = _repo_path(payload.destination or name, allow_missing=True)
    if dest.exists():
        raise HTTPException(status_code=409, detail="Destination already exists")
    dest.parent.mkdir(parents=True, exist_ok=True)

    args = ["clone", "--depth=1", "-b", payload.branch or "main", payload.repo_url, str(dest)]
    result = run_git(args)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["stderr"] or "Git clone failed")
    return {"message": "Repository cloned", "path": dest, **result}


@router.get("/status")
def git_status(
    repo_path: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user),
):
    result = run_git(["status", "--short"], cwd=_repo_path(repo_path))
    lines = result["stdout"].split("\n") if result["stdout"] else []
    changes = []
    for line in lines:
        if line.strip():
            status_code = line[:2].strip()
            file_path = line[3:].strip()
            changes.append({"status": status_code, "file": file_path})
    return {"changes": changes, "branch": run_git(["branch", "--show-current"], cwd=_repo_path(repo_path))["stdout"]}


@router.get("/log")
def git_log(
    repo_path: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(deps.get_current_user),
):
    fmt = "--pretty=format:%H|%an|%ae|%ad|%s"
    result = run_git(["log", fmt, f"-{limit}", "--date=iso"], cwd=_repo_path(repo_path))
    commits = []
    for line in result["stdout"].split("\n"):
        if "|" in line:
            parts = line.split("|", 4)
            if len(parts) == 5:
                commits.append({
                    "hash": parts[0], "author": parts[1], "email": parts[2],
                    "date": parts[3], "message": parts[4],
                })
    return {"commits": commits}


@router.post("/commit")
def git_commit(
    payload: dict,
    current_user: User = Depends(deps.get_current_user),
):
    repo_path = str(_repo_path(payload.get("repo_path")))
    message = payload.get("message", "Auto-commit via AgentForge")
    run_git(["add", "-A"], cwd=repo_path)
    result = run_git(["commit", "-m", message], cwd=repo_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["stderr"] or "Commit failed")
    return {"message": "Committed successfully", **result}


@router.get("/branches")
def git_branches(
    repo_path: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user),
):
    result = run_git(["branch", "-a"], cwd=_repo_path(repo_path))
    branches = [b.strip().lstrip("* ").strip() for b in result["stdout"].split("\n") if b.strip()]
    return {"branches": branches}


@router.post("/checkout")
def git_checkout(
    payload: dict,
    current_user: User = Depends(deps.get_current_user),
):
    branch = payload.get("branch")
    repo_path = payload.get("repo_path")
    if not branch:
        raise HTTPException(status_code=400, detail="Branch name required")
    result = run_git(["checkout", branch], cwd=_repo_path(repo_path))
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["stderr"])
    return {"message": f"Switched to {branch}", **result}
