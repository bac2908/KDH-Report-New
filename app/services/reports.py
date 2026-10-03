from __future__ import annotations

from typing import Any, Dict
from datetime import date

from app.repositories.reports import ReportRepository


class ReportService:
    def __init__(self) -> None:
        self.repository = ReportRepository()

    def get_overview(self, start: date | None = None, end: date | None = None) -> Dict[str, Any]:
        return self.repository.get_overview(start, end)

    def get_seo(self, start: date | None = None, end: date | None = None, filters=None) -> Dict[str, Any]:
        return self.repository.get_seo(start, end, filters)

    def get_facebook_ads(self, **filters) -> Dict[str, Any]:
        return self.repository.get_facebook_ads(**filters)

    def get_report(self, report_type: str, filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return self.repository.get_report(report_type=report_type, filters=filters)
