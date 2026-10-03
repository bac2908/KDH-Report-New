from __future__ import annotations

from typing import Any, Dict, List

from pydantic import BaseModel, Field


class KPIItem(BaseModel):
    key: str
    label: str
    value: float | int
    delta: float | int
    unit: str | None = None
    trend: str = "up"


class OverviewResponse(BaseModel):
    report_type: str = "overview"
    generated_at: str
    metrics: List[KPIItem] = Field(default_factory=list)
    charts: Dict[str, Any] = Field(default_factory=dict)


class ReportResponse(BaseModel):
    report_type: str
    generated_at: str
    data: Dict[str, Any] = Field(default_factory=dict)
    filters: Dict[str, Any] = Field(default_factory=dict)
