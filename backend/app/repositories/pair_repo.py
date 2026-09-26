
from sqlalchemy import distinct, exists, select
from sqlalchemy.orm import Session

from app.models.models import Label, Pair


def get_next_pair(db: Session, annotator_id: str) -> Pair | None:
    """
    Retrieve the next prompt-response pair that this annotator has NOT labeled yet.
    Orders deterministically by pair ID.
    """
    stmt = (
        select(Pair)
        .where(
            ~exists(
                select(1).where(
                    Label.pair_id == Pair.id,
                    Label.annotator_id == annotator_id
                )
            )
        )
        .order_by(Pair.id.asc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()

def get_pair(db: Session, pair_id: int) -> Pair | None:
    """Retrieve a single pair by primary key ID."""
    return db.get(Pair, pair_id)

def count_pairs(db: Session) -> int:
    """Return total number of pairs in database."""
    return db.query(Pair).count()

def list_categories(db: Session) -> list[str]:
    """Return sorted distinct categories in the pairs table."""
    stmt = select(distinct(Pair.category)).order_by(Pair.category)
    return [row[0] for row in db.execute(stmt).all() if row[0]]
