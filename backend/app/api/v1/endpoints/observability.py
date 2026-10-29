from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api import deps
from app.core.database import get_db
from app.core.websocket_manager import ws_manager
from app.models.job import Job
from app.models.models import Analysis, Chat, Message
from app.models.user import User

try:
    import psutil  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - optional dependency
    psutil = None

router = APIRouter()


@router.get("/metrics")
def get_metrics(current_user: User = Depends(deps.get_current_user), db: Session = Depends(get_db)):
    """Return basic observability metrics."""
    total_calls = db.query(Message).count()
    total_tokens = sum((row[0] or 0) for row in db.query(Message.tokens_used).all())
    completed_jobs = db.query(Job).filter(Job.started_at.isnot(None), Job.completed_at.isnot(None)).all()
    latencies = [max(0.0, (job.completed_at - job.started_at).total_seconds() * 1000) for job in completed_jobs if job.started_at and job.completed_at]
    cpu_usage = psutil.cpu_percent(interval=None) if psutil else None
    memory_usage = psutil.virtual_memory().percent if psutil else None
    return {
        "total_calls": total_calls,
        "tokens_used": total_tokens,
        "average_latency_ms": round(sum(latencies) / len(latencies), 2) if latencies else None,
        "error_rate": round((db.query(Job).filter(Job.status == "failed").count() / max(db.query(Job).count(), 1)) * 100, 2),
        "providers": {
            "ai_chats": db.query(Chat).count(),
            "job_queue": db.query(Job).count(),
            "analyses": db.query(Analysis).count(),
        },
        "cpu_usage": cpu_usage,
        "memory_usage": memory_usage,
        "websocket_connections": ws_manager.active_connections_count(),
        "timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/health")
def health_status():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "api": "up",
            "database": "up",
            "websocket": "up",
        }
    }
