import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Finding(Base):
    __tablename__ = "findings"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    review_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_runs.id"), nullable=False, index=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    category: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    endpoint: Mapped[str] = mapped_column(String(2048), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    remediation: Mapped[str] = mapped_column(Text, nullable=False, default="")
    confidence: Mapped[str | None] = mapped_column(String(64), nullable=True)
    evidence_excerpt: Mapped[str | None] = mapped_column(Text, nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
