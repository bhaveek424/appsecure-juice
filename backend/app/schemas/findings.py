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


class ScannerFindingDetail(BaseModel):
    alert: str
    description: str
    remediation: str
    confidence: str | None
    evidence_excerpt: str | None


class FindingDetail(FindingResponse):
    review_run_id: str
    scanner: ScannerFindingDetail | None = None


class UpdateDispositionRequest(BaseModel):
    disposition: ReviewDisposition


class DispositionResponse(BaseModel):
    id: str
    disposition: str
