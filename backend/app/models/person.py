"""
Person profile ORM model.

Stores long-term identity profiles with physical measurements and vector DB references.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    display_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Auto-generated or operator-assigned name"
    )

    # Temporal data
    first_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Physical measurements
    height_cm: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Estimated height in centimeters"
    )
    height_confidence: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Confidence of height estimate (0-1)"
    )
    body_ratios: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Scale-invariant body proportions: shoulder_hip, torso_leg, etc."
    )

    # Qdrant vector references
    qdrant_appearance_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Qdrant point ID for appearance embedding"
    )
    qdrant_gait_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="Qdrant point ID for gait embedding"
    )

    # Aggregate stats
    total_crossings: Mapped[int] = mapped_column(Integer, default=0)
    total_entries: Mapped[int] = mapped_column(Integer, default=0)
    total_exits: Mapped[int] = mapped_column(Integer, default=0)

    # Metadata
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    crossing_events = relationship("CrossingEvent", back_populates="person")

    def __repr__(self):
        return f"<Person {self.display_name or 'Unknown'} ({self.id})>"
