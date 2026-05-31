"""
Bag observation ORM model.

Links detected bag counts and types to specific crossing events.
"""

import uuid
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BagType(str, enum.Enum):
    BACKPACK = "backpack"
    HANDBAG = "handbag"
    SUITCASE = "suitcase"


class BagObservation(Base):
    __tablename__ = "bag_observations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    crossing_event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crossing_events.id", ondelete="CASCADE"),
        nullable=False,
    )

    bag_type: Mapped[BagType] = mapped_column(Enum(BagType), nullable=False)
    count: Mapped[int] = mapped_column(Integer, default=1)
    confidence: Mapped[float] = mapped_column(
        Float, default=0.0, comment="Detection confidence for this bag (0-1)"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    crossing_event = relationship("CrossingEvent", back_populates="bag_observations")

    def __repr__(self):
        return f"<BagObservation {self.bag_type.value} x{self.count}>"
