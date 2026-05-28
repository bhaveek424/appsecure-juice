from pydantic import BaseModel


class SourceObservationResponse(BaseModel):
    finding_id: str
    title: str
    severity: str


class HypothesisResponse(BaseModel):
    id: str
    title: str
    rationale: str
    recommended_skill_id: str
    recommended_skill_name: str
    priority: str
    source_observations: list[SourceObservationResponse]
