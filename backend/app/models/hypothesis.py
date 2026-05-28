import uuid

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Hypothesis(Base):
    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    review_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_runs.id"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_skill_id: Mapped[str] = mapped_column(String(64), nullable=False)
    recommended_skill_name: Mapped[str] = mapped_column(String(128), nullable=False)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    source_observations_json: Mapped[str] = mapped_column(Text, nullable=False)
