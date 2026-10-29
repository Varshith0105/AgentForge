import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from app.core.database import get_db
from app.api import deps
from app.models.user import User
from app.models.job import Job

router = APIRouter()


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    job_type: str
    status: str
    project_id: Optional[str]
    progress: float
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


@router.get("", response_model=List[JobResponse])
def list_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    jobs = db.query(Job).filter(Job.user_id == current_user.id).order_by(Job.created_at.desc()).limit(50).all()
    return jobs


@router.get("/{job_id}", response_model=JobResponse)
def get_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("/{job_id}/cancel")
def cancel_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status in ("completed", "failed"):
        raise HTTPException(status_code=400, detail=f"Cannot cancel a {job.status} job")
    job.status = "cancelled"
    job.completed_at = datetime.now(timezone.utc)
    db.commit()
    return {"message": "Job cancelled", "job_id": job_id}


@router.delete("/{job_id}")
def delete_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(deps.get_current_user),
):
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == current_user.id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
    return {"message": "Job deleted"}
