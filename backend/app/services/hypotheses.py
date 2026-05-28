import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.hypothesis import Hypothesis
from app.reasoning.types import TriageHypothesisResult
from app.schemas.hypotheses import HypothesisResponse, SourceObservationResponse

_PRIORITY_ORDER = {"High": 0, "Medium": 1, "Low": 2, "Informational": 3}


def persist_hypotheses(
    db: Session,
    review_run_id: str,
    triage_results: list[TriageHypothesisResult],
) -> None:
    for result in triage_results:
        db.add(
            Hypothesis(
                review_run_id=review_run_id,
                title=result.title,
                rationale=result.rationale,
                recommended_skill_id=result.recommended_skill_id,
                recommended_skill_name=result.recommended_skill_name,
                priority=result.priority,
                source_observations_json=json.dumps(
                    [ref.model_dump() for ref in result.source_observations]
                ),
            )
        )


def list_hypotheses_for_run(db: Session, review_run_id: str) -> list[HypothesisResponse]:
    rows = db.scalars(
        select(Hypothesis).where(Hypothesis.review_run_id == review_run_id)
    ).all()
    sorted_rows = sorted(
        rows,
        key=lambda row: (_PRIORITY_ORDER.get(row.priority, 99), row.title.lower()),
    )
    return [_to_response(row) for row in sorted_rows]


def _to_response(hypothesis: Hypothesis) -> HypothesisResponse:
    sources = json.loads(hypothesis.source_observations_json)
    return HypothesisResponse(
        id=hypothesis.id,
        title=hypothesis.title,
        rationale=hypothesis.rationale,
        recommended_skill_id=hypothesis.recommended_skill_id,
        recommended_skill_name=hypothesis.recommended_skill_name,
        priority=hypothesis.priority,
        source_observations=[
            SourceObservationResponse.model_validate(source) for source in sources
        ],
    )
