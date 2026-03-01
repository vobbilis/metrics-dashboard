from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

# Type aliases for alerting
AlertOperator = Literal["gt", "lt", "eq"]
AlertState = Literal["ok", "firing"]


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


class AlertRuleIn(BaseModel):
    metric_name: str = Field(..., min_length=1, max_length=128)
    operator: AlertOperator
    threshold: float


class AlertRuleOut(BaseModel):
    id: str
    metric_name: str
    operator: AlertOperator
    threshold: float
    state: AlertState = "ok"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
