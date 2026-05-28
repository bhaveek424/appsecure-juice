from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.findings import (
    DispositionResponse,
    FindingDetail,
    UpdateDispositionRequest,
)
from app.services import findings as finding_service

router = APIRouter(tags=["findings"])


@router.patch(
    "/api/findings/{finding_id}/disposition",
    response_model=DispositionResponse,
)
def update_finding_disposition(
    finding_id: str,
    body: UpdateDispositionRequest,
    db: Session = Depends(get_db),
):
    try:
        return finding_service.update_disposition(
            db, finding_id, body.disposition
        )
    except finding_service.FindingNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        ) from exc
