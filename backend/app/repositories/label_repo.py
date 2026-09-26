
from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models.models import Label, Pair


def create_label(db: Session, pair: Pair, annotator_id: str, chosen: str) -> Label:
    """Create and persist a new preference label inside a database transaction."""
    label = Label(
        pair_id=pair.id,
        annotator_id=annotator_id,
        chosen=chosen,
        prompt=pair.prompt,
        response_a=pair.response_a,
        response_b=pair.response_b,
        category=pair.category,
        labeled_at=func.now()
    )
    db.add(label)
    db.commit()
    db.refresh(label)
    return label

def exists_label(db: Session, pair_id: int, annotator_id: str) -> Label | None:
    """Check if an annotation by this annotator for this pair already exists."""
    stmt = select(Label).where(
        Label.pair_id == pair_id,
        Label.annotator_id == annotator_id
    )
    return db.execute(stmt).scalar_one_or_none()

def count_labels(db: Session) -> int:
    """Count total labels submitted across all annotators."""
    return db.query(func.count(Label.id)).scalar() or 0

def distribution(db: Session) -> dict[str, int]:
    """
    Return distribution dictionary for choices: A, B, tie, skip.
    Guarantees all 4 keys are present even if counts are 0.
    """
    stmt = select(Label.chosen, func.count(Label.id)).group_by(Label.chosen)
    rows = db.execute(stmt).all()
    dist = {"A": 0, "B": 0, "tie": 0, "skip": 0}
    for chosen_val, cnt in rows:
        if chosen_val in dist or chosen_val is not None:
            dist[chosen_val] = cnt
    return dist

def count_distinct_pairs_labeled(db: Session) -> int:
    """Count number of distinct pairs that have at least one label."""
    return db.query(func.count(distinct(Label.pair_id))).scalar() or 0

def count_distinct_annotators(db: Session) -> int:
    """Count number of distinct annotators that have submitted at least one label."""
    return db.query(func.count(distinct(Label.annotator_id))).scalar() or 0

def category_breakdown(db: Session) -> dict[str, int]:
    """Return count of labels by category."""
    stmt = select(Label.category, func.count(Label.id)).group_by(Label.category)
    rows = db.execute(stmt).all()
    return {cat: cnt for cat, cnt in rows if cat}
