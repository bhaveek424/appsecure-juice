from datetime import datetime

from pydantic import BaseModel


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

    model_config = {"from_attributes": True}
