from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.domain.actor_context import ActorContext
from app.models.review_run_actor import ReviewRunActor
from app.target.types import TargetClient


@dataclass(frozen=True)
class StoredActor:
    actor_context: ActorContext
    email: str
    password: str


def _actor_email(review_run_id: str, actor_context: ActorContext) -> str:
    label = actor_context.name.lower()
    return f"{label}-{review_run_id[:8]}@review.local"


def ensure_review_run_actors(
    db: Session,
    review_run_id: str,
    target_client: TargetClient,
) -> dict[ActorContext, StoredActor]:
    actors: dict[ActorContext, StoredActor] = {}
    password = "ReviewPass123!"

    for actor_context in (ActorContext.USER_A, ActorContext.USER_B):
        existing = db.scalars(
            select(ReviewRunActor).where(
                ReviewRunActor.review_run_id == review_run_id,
                ReviewRunActor.actor_label == actor_context.value,
            )
        ).first()

        if existing is None:
            email = _actor_email(review_run_id, actor_context)
            target_client.register_user(email, password)
            db.add(
                ReviewRunActor(
                    review_run_id=review_run_id,
                    actor_label=actor_context.value,
                    email=email,
                    password=password,
                )
            )
            db.commit()
            existing = db.scalars(
                select(ReviewRunActor).where(
                    ReviewRunActor.review_run_id == review_run_id,
                    ReviewRunActor.actor_label == actor_context.value,
                )
            ).one()

        actors[actor_context] = StoredActor(
            actor_context=actor_context,
            email=existing.email,
            password=existing.password,
        )

    return actors
