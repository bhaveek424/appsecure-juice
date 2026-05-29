from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.findings import FindingDetail
from app.schemas.scans import (
    ActiveRunConflict,
    CreateScanRequest,
    CreateScanResponse,
    ScanDetail,
    ScanSummary,
)
from app.schemas.skill_runs import RunRecommendedSkillsResponse, RunSkillResponse
from app.services import cancellation as cancellation_service
from app.services import findings as finding_service
from app.services import review_runs as review_run_service
from app.services import skill_runs as skill_run_service
from app.services.exceptions import (
    ReviewRunNotCancellableError,
    ReviewRunNotFoundError,
    ReviewRunNotReadyError,
    UnknownSkillError,
)

router = APIRouter(prefix="/api/scans", tags=["scans"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CreateScanResponse)
def create_scan(
    background_tasks: BackgroundTasks,
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

    background_tasks.add_task(review_run_service.enqueue_zap_scan, review_run.id)
    return CreateScanResponse(id=review_run.id)


@router.get("", response_model=list[ScanSummary])
def list_scans(db: Session = Depends(get_db)):
    return review_run_service.list_review_runs(db)


@router.post("/{review_run_id}/cancel", response_model=ScanSummary)
def cancel_scan(review_run_id: str, db: Session = Depends(get_db)):
    try:
        return cancellation_service.cancel_review_run(db, review_run_id)
    except ReviewRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review Run not found",
        ) from exc
    except ReviewRunNotCancellableError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review Run cannot be cancelled",
        ) from exc


@router.get("/{review_run_id}", response_model=ScanDetail)
def get_scan(review_run_id: str, db: Session = Depends(get_db)):
    try:
        return review_run_service.get_review_run(db, review_run_id)
    except review_run_service.ReviewRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review Run not found",
        ) from exc


@router.post(
    "/{review_run_id}/skills/run-recommended",
    response_model=RunRecommendedSkillsResponse,
)
def run_recommended_skills(review_run_id: str, db: Session = Depends(get_db)):
    try:
        return skill_run_service.run_recommended_skills(db, review_run_id)
    except ReviewRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review Run not found",
        ) from exc
    except ReviewRunNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review Run is not ready for Review Skills",
        ) from exc


@router.post(
    "/{review_run_id}/skills/{skill_id}/run",
    status_code=status.HTTP_201_CREATED,
    response_model=RunSkillResponse,
)
def run_skill(review_run_id: str, skill_id: str, db: Session = Depends(get_db)):
    try:
        return skill_run_service.run_review_skill(db, review_run_id, skill_id)
    except ReviewRunNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review Run not found",
        ) from exc
    except ReviewRunNotReadyError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Review Run is not ready for Review Skills",
        ) from exc
    except UnknownSkillError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown Review Skill: {skill_id}",
        ) from exc


@router.get(
    "/{review_run_id}/findings/{finding_id}",
    response_model=FindingDetail,
)
def get_scan_finding(
    review_run_id: str,
    finding_id: str,
    db: Session = Depends(get_db),
):
    try:
        return finding_service.get_finding_for_run(db, review_run_id, finding_id)
    except finding_service.FindingNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Finding not found",
        ) from exc
