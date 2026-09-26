import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.models import Label
from app.repositories.label_repo import create_label, exists_label
from app.repositories.pair_repo import get_next_pair, get_pair, list_categories
from app.schemas.schemas import AnalyticsOut, HealthOut, LabelCreate, PairOut
from app.services.analytics_service import get_full_analytics

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/health", response_model=HealthOut, summary="Service & Database Healthcheck")
def health(db: Session = Depends(get_db)):
    """Check backend operational status and database connectivity."""
    try:
        db.execute(text("SELECT 1"))
        return HealthOut(status="ok", database="healthy")
    except Exception as e:
        logger.error(f"Healthcheck database error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "error", "database": "unhealthy", "error": str(e)}
        )

@router.get("/pairs/next", response_model=PairOut, summary="Fetch Next Unlabeled Pair for Annotator")
def next_pair(
    annotator_id: str = Query(..., description="Unique identifier for the annotator"),
    db: Session = Depends(get_db)
):
    """
    Retrieve the next prompt-response pair that this annotator has NOT yet labeled.
    Returns 404 when all pairs have been labeled by this annotator.
    """
    trimmed = annotator_id.strip() if annotator_id else ""
    if not trimmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="annotator_id required"
        )

    pair = get_next_pair(db, trimmed)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No unlabeled pairs available for this annotator."
        )

    return PairOut.model_validate(pair)

@router.get("/pairs/{pair_id}", response_model=PairOut, summary="Retrieve Pair by ID")
def get_pair_by_id(pair_id: int, db: Session = Depends(get_db)):
    """Fetch details of a specific pair by ID."""
    pair = get_pair(db, pair_id)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pair not found"
        )
    return PairOut.model_validate(pair)

@router.post("/labels", status_code=status.HTTP_201_CREATED, summary="Submit Preference Label")
def submit_label(payload: LabelCreate, db: Session = Depends(get_db)):
    """
    Submit a pairwise preference annotation: A, B, tie, or skip.
    Enforces uniqueness per (pair_id, annotator_id) and records completion timestamp.
    """
    annotator_id = payload.annotator_id.strip()
    if not annotator_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="annotator_id required"
        )

    if payload.chosen not in ("A", "B", "tie", "skip"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid chosen value"
        )

    pair = get_pair(db, payload.pair_id)
    if not pair:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pair not found"
        )

    if exists_label(db, payload.pair_id, annotator_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Already labeled"
        )

    try:
        label = create_label(db, pair, annotator_id, payload.chosen)
        logger.info(f"Label recorded: id={label.id}, pair={pair.id}, annotator='{annotator_id}', chosen='{payload.chosen}'")
        return {"id": label.id, "status": "created"}
    except Exception as e:
        db.rollback()
        logger.error(f"Transaction failure submitting label: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record annotation."
        )

@router.get("/analytics", response_model=AnalyticsOut, summary="Platform Analytics & Agreement")
def analytics(db: Session = Depends(get_db)):
    """
    Retrieve platform-wide labeling analytics including choice distribution,
    inter-rater agreement rate, and category breakdowns.
    """
    data = get_full_analytics(db)
    return AnalyticsOut(**data)

def export_generator(
    db: Session,
    category: str | None = None,
    annotator_id: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None
):
    """
    Stream preference records in standard RLHF JSONL format:
    {"prompt": "...", "chosen": "...", "rejected": "...", "metadata": {...}}
    Filters out 'tie' and 'skip' judgments as required for reward model training.
    """
    stmt = select(Label).where(Label.chosen.in_(["A", "B"]))

    if category:
        stmt = stmt.where(Label.category == category)
    if annotator_id:
        stmt = stmt.where(Label.annotator_id == annotator_id)
    if start_date:
        stmt = stmt.where(Label.created_at >= start_date)
    if end_date:
        stmt = stmt.where(Label.created_at <= end_date)

    stmt = stmt.order_by(Label.id.asc())

    # Stream query results efficiently
    labels = db.execute(stmt).scalars()
    for label in labels:
        if label.chosen == "A":
            chosen_txt = label.response_a
            rejected_txt = label.response_b
        else:
            chosen_txt = label.response_b
            rejected_txt = label.response_a

        record = {
            "prompt": label.prompt,
            "chosen": chosen_txt,
            "rejected": rejected_txt,
            "metadata": {
                "category": label.category,
                "annotator_id": label.annotator_id,
                "pair_id": label.pair_id,
                "label_id": label.id,
            },
        }
        yield json.dumps(record, ensure_ascii=False) + "\n"

@router.get("/export", summary="Export Reward-Model Ready Preferences in JSONL")
def export(
    category: str | None = Query(default=None, description="Filter exported records by category"),
    annotator_id: str | None = Query(default=None, description="Filter exported records by annotator ID"),
    start_date: datetime | None = Query(default=None, description="Start date filter (ISO format)"),
    end_date: datetime | None = Query(default=None, description="End date filter (ISO format)"),
    db: Session = Depends(get_db)
):
    """
    Stream reward model preferences formatted as JSON Lines.
    Excludes non-binary preferences (tie/skip) and maps chosen/rejected based on annotator judgments.
    """
    def gen():
        yield from export_generator(
            db=db,
            category=category,
            annotator_id=annotator_id,
            start_date=start_date,
            end_date=end_date
        )

    headers = {
        "Content-Type": "application/x-jsonlines; charset=utf-8",
        "Content-Disposition": 'attachment; filename="labels.jsonl"'
    }
    return StreamingResponse(gen(), media_type="application/x-jsonlines", headers=headers)

@router.get("/categories", response_model=list[str], summary="List Unique Categories")
def categories(db: Session = Depends(get_db)):
    """List all unique prompt categories available in the platform."""
    return list_categories(db)
