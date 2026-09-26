from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PairOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt: str
    response_a: str
    response_b: str
    category: str

class LabelCreate(BaseModel):
    pair_id: int = Field(..., description="ID of the prompt-response pair being labeled")
    annotator_id: str = Field(..., min_length=1, description="Identifier of the annotator submitting the label")
    chosen: str = Field(..., description="Preference choice: A, B, tie, or skip")

    @field_validator("annotator_id")
    @classmethod
    def validate_annotator_id(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("annotator_id cannot be blank or whitespace")
        return trimmed

    @field_validator("chosen")
    @classmethod
    def validate_chosen(cls, v: str) -> str:
        allowed = {"A", "B", "tie", "skip"}
        if v not in allowed:
            raise ValueError(f"chosen must be one of {allowed}, got '{v}'")
        return v

class LabelOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    pair_id: int
    annotator_id: str
    chosen: str | None
    created_at: datetime
    labeled_at: datetime | None
    prompt: str
    response_a: str
    response_b: str
    category: str

class AnalyticsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    total_labels: int
    label_distribution: dict[str, int]
    agreement_rate: float
    total_pairs: int | None = 0
    labeled_pairs: int | None = 0
    active_annotators: int | None = 0
    category_breakdown: dict[str, int] | None = {}

class HealthOut(BaseModel):
    status: str
    database: str
    error: str | None = None
