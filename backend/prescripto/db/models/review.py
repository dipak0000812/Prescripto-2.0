"""
Clinical Review Model.
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from sqlalchemy import String, DateTime, CheckConstraint, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from prescripto.db.base import Base, utc_now


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(50),
        CheckConstraint(
            "status IN ('PENDING_ASSIGNMENT', 'ASSIGNED', 'IN_PROGRESS', 'SUBMITTED', 'ESCALATED')",
            name="chk_review_status",
        ),
        default="PENDING_ASSIGNMENT",
        nullable=False,
    )
    corrections: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"), nullable=True
    )
    notes: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utc_now, nullable=False
    )

    analysis = relationship("Analysis", backref="reviews")
    reviewer = relationship("User", backref="reviews")
