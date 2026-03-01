from datetime import UTC, datetime

from pydantic import BaseModel, Field


class MetricIn(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    value: float
    tags: dict[str, str] = Field(default_factory=dict)


class MetricOut(BaseModel):
    id: str
    name: str
    value: float
    tags: dict[str, str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))


class MetricSummary(BaseModel):
    unique_names: int
    total_data_points: int
