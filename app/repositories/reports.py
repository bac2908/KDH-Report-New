from __future__ import annotations

from typing import Any, Dict
from datetime import date

from app.integrations.mock.generator import build_overview_payload, build_report_payload


class ReportRepository:
    def get_overview(self, start: date | None = None, end: date | None = None) -> Dict[str, Any]:
        return build_overview_payload(start, end)

    def get_seo(self, start: date | None = None, end: date | None = None, filters=None) -> Dict[str, Any]:
        from app.integrations.mock.seo import seo_payload

        return seo_payload(start, end, filters)

    def get_facebook_ads(self, **filters) -> Dict[str, Any]:
        from app.integrations.mock.facebook_ads import facebook_ads_payload
        return facebook_ads_payload(**filters)

    def get_report(self, report_type: str, filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
        return build_report_payload(report_type=report_type, filters=filters or {})
