import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ReviewRunActor(Base):
    __tablename__ = "review_run_actors"
    __table_args__ = (
        UniqueConstraint("review_run_id", "actor_label", name="uq_review_run_actor"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    review_run_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("review_runs.id"), nullable=False, index=True
    )
    actor_label: Mapped[str] = mapped_column(String(16), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
