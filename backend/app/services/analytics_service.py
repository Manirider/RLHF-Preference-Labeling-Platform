"""
Analytics service for label metrics and inter-rater agreement calculation.
"""
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.models import Label
from app.repositories.label_repo import (
    category_breakdown,
    count_distinct_annotators,
    count_distinct_pairs_labeled,
    count_labels,
    distribution,
)
from app.repositories.pair_repo import count_pairs


def compute_agreement(db: Session) -> float:
    """
    Computes inter-rater agreement rate across prompt-response pairs evaluated by multiple annotators.

    Formula:
      For every pair p with at least 2 annotations (N_p >= 2):
        - Identify the majority label count M_p = max_c (count of choice c in pair p)
        - Aggregate total annotations across multi-annotator pairs: T = sum(N_p)
        - Aggregate agreeing annotations: A = sum(M_p)
      Agreement rate = A / T (or 0.0 if no pairs have >= 2 annotations).

    Guarantees:
      - Returns a float strictly in [0.0, 1.0].
      - If 3 annotators all select 'A' on a pair, agreement_rate = 1.0.
      - Fully deterministic and handles any combination of choices.
    """
    stmt = select(Label.pair_id, Label.chosen).where(Label.chosen.isnot(None))
    rows = db.execute(stmt).all()

    pair_votes: dict[int, list] = {}
    for pair_id, chosen in rows:
        pair_votes.setdefault(pair_id, []).append(chosen)

    total_multi_votes = 0
    total_majority_votes = 0

    for votes in pair_votes.values():
        if len(votes) < 2:
            continue
        counts: dict[str, int] = {}
        for v in votes:
            counts[v] = counts.get(v, 0) + 1
        majority = max(counts.values()) if counts else 0
        total_majority_votes += majority
        total_multi_votes += len(votes)

    if total_multi_votes == 0:
        return 0.0

    return round(float(total_majority_votes) / float(total_multi_votes), 4)

def get_full_analytics(db: Session) -> dict[str, Any]:
    """Retrieve full analytics bundle for the platform."""
    total = count_labels(db)
    dist = distribution(db)
    agreement = compute_agreement(db)
    total_pairs = count_pairs(db)
    labeled_pairs = count_distinct_pairs_labeled(db)
    active_annotators = count_distinct_annotators(db)
    cat_dist = category_breakdown(db)

    return {
        "total_labels": total,
        "label_distribution": dist,
        "agreement_rate": agreement,
        "total_pairs": total_pairs,
        "labeled_pairs": labeled_pairs,
        "active_annotators": active_annotators,
        "category_breakdown": cat_dist
    }
