from typing import Protocol

from pydantic import BaseModel, Field


class SanitizedObservation(BaseModel):
    finding_id: str
    title: str
    severity: str
    category: str
    endpoint: str
    source: str


class SourceObservationRef(BaseModel):
    finding_id: str
    title: str
    severity: str


class TriageHypothesisResult(BaseModel):
    title: str
    rationale: str
    recommended_skill_id: str
    recommended_skill_name: str
    priority: str
    source_observations: list[SourceObservationRef] = Field(default_factory=list)


class ReasoningClient(Protocol):
    def triage(
        self, observations: list[SanitizedObservation]
    ) -> list[TriageHypothesisResult]: ...
