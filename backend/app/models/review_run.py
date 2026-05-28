import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base
from app.domain.review_run_status import ReviewRunStatus


class ReviewRun(Base):
    __tablename__ = "review_runs"
    __table_args__ = (
        Index(
            "uq_review_runs_one_active",
            "is_active",
            unique=True,
            sqlite_where=text("is_active = 1"),
        ),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default=ReviewRunStatus.QUEUED
    )
    target_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    current_step: Mapped[str] = mapped_column(
        String(255), nullable=False, default="Queued"
    )
    progress: Mapped[float | None] = mapped_column(nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="0"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
