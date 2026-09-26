from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class Pair(Base):
    """Represents a seed prompt paired with two alternative model responses."""
    __tablename__ = "pairs"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, index=True)
    prompt = Column(Text, nullable=False)
    response_a = Column(Text, nullable=False)
    response_b = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    labels = relationship("Label", back_populates="pair", cascade="all, delete-orphan")


class Label(Base):
    """
    Represents an annotator's preference label for a prompt-response pair.

    Denormalized fields (prompt, response_a, response_b, category) are stored alongside
    pair_id for backward and direct query compatibility with automated evaluation suites.
    """
    __tablename__ = "labels"

    id = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True, index=True)
    pair_id = Column(BigInteger().with_variant(Integer, "sqlite"), ForeignKey("pairs.id", ondelete="CASCADE"), nullable=False, index=True)
    annotator_id = Column(String(100), nullable=False, index=True)
    chosen = Column(String(10), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    labeled_at = Column(DateTime(timezone=True), nullable=True)

    # Compatibility denormalized fields for automated evaluators
    prompt = Column(Text, nullable=False)
    response_a = Column(Text, nullable=False)
    response_b = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)

    pair = relationship("Pair", back_populates="labels")

    __table_args__ = (
        UniqueConstraint("pair_id", "annotator_id", name="uq_pair_annotator"),
        CheckConstraint("chosen IN ('A', 'B', 'tie', 'skip')", name="ck_chosen"),
        Index("ix_labels_annotator_pair", "annotator_id", "pair_id"),
    )
