from datetime import datetime

from pydantic import BaseModel


class EvidencePacketResponse(BaseModel):
    id: str
    skill_id: str
    scenario: str
    actor_context: str
    expected_behavior: str
    observed_behavior: str
    request_method: str
    request_path: str
    response_status: int
    response_excerpt: str
    reasoning_summary: str
    captured_at: datetime

    model_config = {"from_attributes": True}


class SkillRunResponse(BaseModel):
    id: str
    skill_id: str
    status: str
    outcome: str | None
    summary: str
    inconclusive_reason: str | None
    finding_id: str | None
    started_at: datetime
    completed_at: datetime | None
    evidence_packets: list[EvidencePacketResponse]

    model_config = {"from_attributes": True}


class RunSkillResponse(BaseModel):
    skill_run: SkillRunResponse
