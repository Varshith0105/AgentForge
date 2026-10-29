import ast
import os
import re
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.models import Project, Analysis

router = APIRouter()


class AnalysisStartRequest(BaseModel):
    project_id: str
    analysis_type: Optional[str] = "full"


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    status: str
    analysis_type: str
    created_at: datetime


@router.post("/start")
async def start_analysis(
    payload: AnalysisStartRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    project = db.query(Project).filter(
        Project.id == payload.project_id,
        Project.owner_id == current_user.id
    ).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    analysis = Analysis(
        id=str(uuid.uuid4()),
        project_id=payload.project_id,
        status="running",
        analysis_type=payload.analysis_type or "full",
        started_at=datetime.utcnow(),
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    repo_path = str(getattr(project, "repo_path", "") or "")
    background_tasks.add_task(_run_real_analysis, analysis.id, project.id, repo_path)

    return {
        "analysis_id": analysis.id,
        "status": "started",
        "message": "Analysis started — parsing repository with AST engine.",
    }


def _run_real_analysis(analysis_id: str, project_id: str, repo_path: Optional[str]):
    """Background real analysis task using the platform engine."""
    from app.core.database import SessionLocal
    from app.services.platform_engine import repository_stats, build_knowledge_graph

    db = SessionLocal()
    try:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if not analysis:
            return

        result = {
            "summary": "No repository path available.",
            "files_analyzed": 0,
            "total_lines": 0,
            "total_functions": 0,
            "total_classes": 0,
            "security_score": 100,
            "quality_score": 100,
            "bugs": [],
            "security_issues": [],
            "dependencies": [],
            "language_breakdown": {},
        }

        if repo_path and os.path.exists(repo_path):
            stats = repository_stats(repo_path)
            bugs = _scan_bugs(repo_path)
            security_issues = _scan_security(repo_path)
            deps_list = _scan_dependencies(repo_path)

            # Score: deduct points for issues found
            raw_security = max(0, 100 - len(security_issues) * 8)
            raw_quality = max(0, 100 - len(bugs) * 3)

            result = {
                "summary": (
                    f"Analyzed {stats['total_files']} files, "
                    f"{stats['total_lines']} lines, "
                    f"{stats['total_functions']} functions, "
                    f"{stats['total_classes']} classes."
                ),
                "files_analyzed": stats["total_files"],
                "total_lines": stats["total_lines"],
                "total_functions": stats["total_functions"],
                "total_classes": stats["total_classes"],
                "security_score": raw_security,
                "quality_score": raw_quality,
                "bugs": bugs[:30],
                "security_issues": security_issues[:20],
                "dependencies": deps_list[:50],
                "language_breakdown": stats.get("language_counts", {}),
                "largest_files": stats.get("largest_files", [])[:5],
            }

        analysis.status = "completed"
        analysis.result_json = result
        analysis.completed_at = datetime.utcnow()

        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.is_analyzed = True
            project.status = "analyzed"

        db.commit()
    except Exception as e:
        analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
        if analysis:
            analysis.status = "failed"
            analysis.error_message = str(e)
            db.commit()
    finally:
        db.close()


def _scan_bugs(repo_path: str) -> list:
    """Scan repository for common bug patterns."""
    bugs = []
    skip_dirs = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__"}

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if not fname.endswith(".py"):
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, repo_path).replace("\\", "/")
            try:
                source = open(fpath, encoding="utf-8", errors="ignore").read()
                lines = source.splitlines()
            except Exception:
                continue

            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # Bare except
                if re.match(r"^except\s*:", stripped):
                    bugs.append({"file": rel_path, "line": i, "type": "bare-except",
                                 "message": "Bare `except:` clause catches all exceptions silently",
                                 "severity": "warning", "snippet": stripped})
                # TODO/FIXME
                if re.search(r"\b(TODO|FIXME|HACK|XXX)\b", stripped, re.IGNORECASE):
                    bugs.append({"file": rel_path, "line": i, "type": "todo",
                                 "message": f"Unresolved marker: {stripped[:80]}",
                                 "severity": "info", "snippet": stripped})
                # Mutable default argument
                if re.match(r"def\s+\w+\s*\(.*=\s*(\[\]|\{\}|\(\))", stripped):
                    bugs.append({"file": rel_path, "line": i, "type": "mutable-default",
                                 "message": "Mutable default argument — shared across calls",
                                 "severity": "error", "snippet": stripped})
            # Try AST for complexity
            try:
                tree = ast.parse(source)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        complexity = sum(1 for n in ast.walk(node)
                                         if isinstance(n, (ast.If, ast.For, ast.While, ast.ExceptHandler, ast.With)))
                        if complexity > 10:
                            bugs.append({"file": rel_path, "line": node.lineno, "type": "high-complexity",
                                         "message": f"Function `{node.name}` has cyclomatic complexity ~{complexity}",
                                         "severity": "warning", "snippet": f"def {node.name}(..."})
            except Exception:
                pass
    return bugs


def _scan_security(repo_path: str) -> list:
    """Scan repository for common security issues."""
    issues = []
    skip_dirs = {".git", "node_modules", "dist", "build", ".venv", "venv", "__pycache__"}
    text_exts = {".py", ".js", ".ts", ".tsx", ".jsx", ".env", ".yaml", ".yml", ".json", ".sh"}

    secret_patterns = [
        (r'(password|passwd|pwd)\s*=\s*["\'][^"\']{6,}["\']', "Hardcoded password"),
        (r'(api_key|apikey|secret_key|secret)\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded API key/secret"),
        (r'(token)\s*=\s*["\'][^"\']{10,}["\']', "Hardcoded token"),
        (r'eval\s*\(', "Use of eval() — potential code injection"),
        (r'exec\s*\(', "Use of exec() — potential code injection"),
        (r'subprocess\.call\s*\(.*shell\s*=\s*True', "Shell injection risk: subprocess with shell=True"),
        (r'\.format\s*\(.*request\b', "Potential injection in string format with user input"),
        (r'sqlite3\.connect\s*\(.*request', "Direct DB connection with user input"),
    ]

    for root, dirs, files in os.walk(repo_path):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            ext = os.path.splitext(fname)[1].lower()
            if ext not in text_exts:
                continue
            fpath = os.path.join(root, fname)
            rel_path = os.path.relpath(fpath, repo_path).replace("\\", "/")
            try:
                source = open(fpath, encoding="utf-8", errors="ignore").read()
                lines = source.splitlines()
            except Exception:
                continue
            for pattern, label in secret_patterns:
                for i, line in enumerate(lines, 1):
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append({
                            "file": rel_path, "line": i, "type": "security",
                            "message": label, "severity": "high",
                            "snippet": line.strip()[:120],
                        })
    return issues


def _scan_dependencies(repo_path: str) -> list:
    """Extract dependencies from requirements.txt, package.json, pyproject.toml, etc."""
    deps_found = []
    dep_files = ["requirements.txt", "package.json", "pyproject.toml", "Pipfile", "go.mod", "Cargo.toml"]

    for dep_file in dep_files:
        fpath = os.path.join(repo_path, dep_file)
        if not os.path.exists(fpath):
            continue
        try:
            content = open(fpath, encoding="utf-8", errors="ignore").read()
            if dep_file == "requirements.txt":
                for line in content.splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        deps_found.append({"file": dep_file, "name": line, "type": "python"})
            elif dep_file == "package.json":
                import json
                pkg = json.loads(content)
                for dep, ver in {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}.items():
                    deps_found.append({"file": dep_file, "name": dep, "version": ver, "type": "nodejs"})
        except Exception:
            pass
    return deps_found


@router.get("/status/{analysis_id}")
def get_analysis_status(
    analysis_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {
        "id": analysis.id,
        "status": analysis.status,
        "result": analysis.result_json,
        "error": analysis.error_message,
        "created_at": analysis.created_at,
        "completed_at": analysis.completed_at,
    }


@router.post("/upload")
async def upload_repository(
    file: UploadFile = File(...),
    project_id: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Upload a zip file of a repository for analysis."""
    import zipfile
    import shutil

    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are supported")

    upload_dir = os.path.join("uploads", str(current_user.id))
    os.makedirs(upload_dir, exist_ok=True)

    zip_path = os.path.join(upload_dir, file.filename)
    with open(zip_path, "wb") as f:
        content = await file.read()
        f.write(content)

    extract_path = os.path.join(upload_dir, file.filename.replace(".zip", ""))
    os.makedirs(extract_path, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_path)

    if project_id:
        project = db.query(Project).filter(Project.id == project_id).first()
        if project:
            project.repo_path = extract_path
            project.status = "ready"
    else:
        project = Project(
            id=str(uuid.uuid4()),
            name=file.filename.replace(".zip", ""),
            owner_id=current_user.id,
            repo_path=extract_path,
            status="ready",
        )
        db.add(project)

    db.commit()
    project_id = project.id if project else None
    file_count = sum(1 for _, _, files in os.walk(extract_path) for _ in files)

    return {
        "message": "Repository uploaded successfully",
        "project_id": project_id,
        "files_count": file_count,
        "path": extract_path,
    }
