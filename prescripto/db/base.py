"""
SQLAlchemy 2.0 Base Configuration and Common Mixins.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    metadata = MetaData()


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(default=utc_now)
