import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, JSON
from app.core.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False, default="User")
    password_hash = Column(String, nullable=False)
    role = Column(String, nullable=False, default="developer")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String, nullable=True)
    github_username = Column(String, nullable=True)
    preferences_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
