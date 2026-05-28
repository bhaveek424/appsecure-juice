import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class EvidencePacket(Base):
    __tablename__ = "evidence_packets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    skill_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("skill_runs.id"), nullable=False, index=True
    )
    finding_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("findings.id"), nullable=True
    )
    skill_id: Mapped[str] = mapped_column(String(64), nullable=False)
    scenario: Mapped[str] = mapped_column(String(255), nullable=False)
    actor_context: Mapped[str] = mapped_column(String(32), nullable=False)
    expected_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    observed_behavior: Mapped[str] = mapped_column(Text, nullable=False)
    request_method: Mapped[str] = mapped_column(String(16), nullable=False)
    request_path: Mapped[str] = mapped_column(String(2048), nullable=False)
    response_status: Mapped[int] = mapped_column(Integer, nullable=False)
    response_excerpt: Mapped[str] = mapped_column(Text, nullable=False, default="")
    reasoning_summary: Mapped[str] = mapped_column(Text, nullable=False, default="")
    captured_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
