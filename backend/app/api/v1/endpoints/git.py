import subprocess
import os
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.api import deps
from app.models.user import User

router = APIRouter()


class GitCommandRequest(BaseModel):
    command: str
    repo_path: Optional[str] = None
    args: Optional[List[str]] = None


class GitCloneRequest(BaseModel):
    repo_url: str
    branch: Optional[str] = "main"
    destination: Optional[str] = None


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
    dest = payload.destination or os.path.join("repos", payload.repo_url.split("/")[-1].replace(".git", ""))
    os.makedirs(os.path.dirname(dest) if "/" in dest else "repos", exist_ok=True)

    args = ["clone", "--depth=1", "-b", payload.branch or "main", payload.repo_url, dest]
    result = run_git(args)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["stderr"] or "Git clone failed")
    return {"message": "Repository cloned", "path": dest, **result}


@router.get("/status")
def git_status(
    repo_path: Optional[str] = None,
    current_user: User = Depends(deps.get_current_user),
):
    result = run_git(["status", "--short"], cwd=repo_path)
    lines = result["stdout"].split("\n") if result["stdout"] else []
    changes = []
    for line in lines:
        if line.strip():
            status_code = line[:2].strip()
            file_path = line[3:].strip()
            changes.append({"status": status_code, "file": file_path})
    return {"changes": changes, "branch": run_git(["branch", "--show-current"], cwd=repo_path)["stdout"]}


@router.get("/log")
def git_log(
    repo_path: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(deps.get_current_user),
):
    fmt = "--pretty=format:%H|%an|%ae|%ad|%s"
    result = run_git(["log", fmt, f"-{limit}", "--date=iso"], cwd=repo_path)
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
    repo_path = payload.get("repo_path")
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
    result = run_git(["branch", "-a"], cwd=repo_path)
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
    result = run_git(["checkout", branch], cwd=repo_path)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["stderr"])
    return {"message": f"Switched to {branch}", **result}
