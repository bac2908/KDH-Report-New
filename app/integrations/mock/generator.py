from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any, Dict, List


def build_overview_payload(start: date | None = None, end: date | None = None) -> Dict[str, Any]:
    from app.integrations.mock.overview import overview_payload

    return overview_payload(start, end)


def build_report_payload(report_type: str, filters: Dict[str, Any] | None = None) -> Dict[str, Any]:
    filters = filters or {}
    now = datetime.now(timezone.utc).isoformat()
    payload = {
        "report_type": report_type,
        "generated_at": now,
        "data": {
            "summary": {
                "title": f"{report_type.replace('-', ' ').title()} report",
                "status": "healthy",
                "items": [
                    {"label": "Impressions", "value": 482000},
                    {"label": "CTR", "value": "3.8%"},
                ],
            },
            "series": {
                "labels": ["W1", "W2", "W3", "W4"],
                "values": [34, 41, 38, 49],
            },
        },
        "filters": filters,
    }
    return payload
