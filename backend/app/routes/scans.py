from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.scans import (
    ActiveRunConflict,
    CreateScanRequest,
    CreateScanResponse,
    ScanDetail,
    ScanSummary,
)
from app.services import review_runs as review_run_service

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateScanResponse)
def create_scan(
    body: CreateScanRequest = Body(default_factory=CreateScanRequest),
    db: Session = Depends(get_db),
):
    try:
        review_run = review_run_service.create_review_run(db, target=body.target)
    except review_run_service.TargetNotAllowedError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target does not match the configured Target Application",
        ) from exc
    except review_run_service.ActiveReviewRunExistsError as exc:
        conflict = ActiveRunConflict(
            detail="A Review Run is already active",
            active_run_id=exc.active_run_id,
        )
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict.model_dump(),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    return CreateScanResponse(id=review_run.id)


@router.get("", response_model=list[ScanSummary])
def list_scans(db: Session = Depends(get_db)):
    return review_run_service.list_review_runs(db)


@router.get("/{review_run_id}", response_model=ScanDetail)
def get_scan(review_run_id: str, db: Session = Depends(get_db)):
    try:
        return review_run_service.get_review_run(db, review_run_id)
    except review_run_service.ReviewRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review Run not found",
        ) from exc
