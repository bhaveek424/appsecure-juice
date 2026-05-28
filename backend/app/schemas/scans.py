from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.findings import FindingResponse
from app.schemas.hypotheses import HypothesisResponse
from app.schemas.skill_runs import SkillRunResponse


class CreateScanRequest(BaseModel):
    target: str | None = None


class CreateScanResponse(BaseModel):
    id: str


class FindingCounts(BaseModel):
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    informational: int = 0


class ScanSummary(BaseModel):
    id: str
    status: str
    started_at: datetime
    completed_at: datetime | None
    current_step: str
    finding_counts: FindingCounts


class ScanDetail(BaseModel):
    id: str
    status: str
    progress: float | None
    current_step: str
    findings: list[FindingResponse] = Field(default_factory=list)
    hypotheses: list[HypothesisResponse] = Field(default_factory=list)
    skill_runs: list[SkillRunResponse] = Field(default_factory=list)


class ActiveRunConflict(BaseModel):
    detail: str
    active_run_id: str
