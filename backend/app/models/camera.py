"""
Camera configuration ORM model.

Stores camera source, calibration matrices, and boundary line coordinates.
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Camera(Base):
    __tablename__ = "cameras"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_url: Mapped[str] = mapped_column(
        Text, nullable=False, comment="USB device index or RTSP URL"
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Calibration parameters
    intrinsic_matrix: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="3x3 camera intrinsic matrix as nested list"
    )
    homography_matrix: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="3x3 ground-plane homography matrix"
    )
    camera_height_m: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Camera mounting height in meters"
    )
    tilt_deg: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Camera tilt/depression angle in degrees"
    )
    focal_length_px: Mapped[float | None] = mapped_column(
        Float, nullable=True, comment="Focal length in pixels"
    )
    principal_point: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True, comment="Principal point [cx, cy] in pixels"
    )

    # Boundary line definition
    boundary_line: Mapped[dict | None] = mapped_column(
        JSONB, nullable=True,
        comment="Two points defining boundary: {start: [x,y], end: [x,y]}"
    )

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    crossing_events = relationship("CrossingEvent", back_populates="camera")

    def __repr__(self):
        return f"<Camera {self.name} ({self.id})>"
