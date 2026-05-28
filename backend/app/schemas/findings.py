from datetime import datetime

from pydantic import BaseModel, Field

from app.domain.review_disposition import ReviewDisposition


class FindingResponse(BaseModel):
    id: str
    source: str
    title: str
    category: str
    severity: str
    endpoint: str
    description: str
    remediation: str
    confidence: str | None
    evidence_excerpt: str | None
    discovered_at: datetime
    disposition: str

    model_config = {"from_attributes": True}


class BusinessLogicEvidenceDetail(BaseModel):
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


class ScannerFindingDetail(BaseModel):
    alert: str
    description: str
    remediation: str
    confidence: str | None
    evidence_excerpt: str | None


class FindingDetail(FindingResponse):
    review_run_id: str
    scanner: ScannerFindingDetail | None = None
    business_logic: BusinessLogicEvidenceDetail | None = None


class UpdateDispositionRequest(BaseModel):
    disposition: ReviewDisposition


class DispositionResponse(BaseModel):
    id: str
    disposition: str
