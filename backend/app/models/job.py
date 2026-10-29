import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, Integer, Text, DateTime, JSON
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    job_type = Column(String, nullable=False)  # analysis, agent, rag_index, etc.
    status = Column(String, default="pending")  # pending, running, completed, failed, cancelled
    project_id = Column(String, nullable=True)
    user_id = Column(String, nullable=True)
    progress = Column(Float, default=0.0)
    result_json = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    logs = Column(Text, nullable=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
