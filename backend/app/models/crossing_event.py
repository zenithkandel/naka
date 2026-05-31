"""
Crossing event ORM model.

Logs each boundary crossing with direction, match type, fusion scores,
and human review status.
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import (
    Boolean, DateTime, Enum, Float, ForeignKey, String, func
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Direction(str, enum.Enum):
    IN = "IN"
    OUT = "OUT"


class MatchType(str, enum.Enum):
    POSITIVE = "POSITIVE"
    CANDIDATE = "CANDIDATE"
    NEW = "NEW"


class CrossingEvent(Base):
    __tablename__ = "crossing_events"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # Foreign keys
    camera_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("cameras.id", ondelete="CASCADE"),
        nullable=False
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("persons.id", ondelete="SET NULL"),
        nullable=True
    )

    # Event data
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    direction: Mapped[Direction] = mapped_column(
        Enum(Direction), nullable=False
    )

    # Identity fusion results
    match_type: Mapped[MatchType] = mapped_column(
        Enum(MatchType), nullable=False, default=MatchType.NEW
    )
    fusion_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Combined identity fusion score (0-1)"
    )
    coverage_score: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Fraction of feature channels available (0-1)"
    )

    # Human review
    needs_review: Mapped[bool] = mapped_column(Boolean, default=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Track metadata
    track_id: Mapped[int | None] = mapped_column(
        comment="BoT-SORT track ID for this session"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    camera = relationship("Camera", back_populates="crossing_events")
    person = relationship("Person", back_populates="crossing_events")
    bag_observations = relationship(
        "BagObservation", back_populates="crossing_event", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<CrossingEvent {self.direction.value} @ {self.timestamp}>"
