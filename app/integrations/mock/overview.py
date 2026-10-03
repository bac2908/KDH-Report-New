"""Deterministic demonstration data based on the supplied KinderHealth design.

Other ranges are proportional illustrations, not connected marketing analytics.
"""
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
import json
from pathlib import Path
import re

DEFAULT_START = date(2026, 9, 1)
DEFAULT_END = date(2026, 9, 30)
MIN_DATE = date(2026, 4, 1)
METRICS = [
    ("reach", "Tổng lượt tiếp cận", 482350, 15.8, ""),
    ("traffic", "Lượt truy cập Website", 68420, 22.4, ""),
    ("engagement", "Tổng lượt tương tác", 34190, 9.1, ""),
    ("leads", "Khách hàng tiềm năng", 1247, 18.4, ""),
    ("spend", "Tổng chi phí quảng cáo", 48650000, -4.2, "₫"),
]


@lru_cache
def sample_fields():
    return json.loads(Path(__file__).with_name("overview_fields.json").read_text(encoding="utf-8"))


def format_number(value):
    return f"{round(value):,}".replace(",", ".")


def validate_range(start: date, end: date):
    if start > end:
        raise ValueError("Ngày bắt đầu phải trước hoặc bằng ngày kết thúc.")
    if start < MIN_DATE or end > DEFAULT_END:
        raise ValueError("Dữ liệu mẫu hỗ trợ từ 01/04/2026 đến 30/09/2026.")


def overview_payload(start: date | None = None, end: date | None = None):
    start, end = start or DEFAULT_START, end or DEFAULT_END
    validate_range(start, end)
    days = (end - start).days + 1
    ratio = days / 30
    fields = {}
    # Match whole numeric tokens so percentages such as 19,5% remain unchanged.
    number = re.compile(r"\d[\d.,]*%?")
    for key, definition in sample_fields().items():
        def scale(match):
            token = match.group()
            if token.endswith("%") or "," in token:
                return token
            return format_number(int(token.replace(".", "")) * ratio)
        fields[key] = number.sub(scale, definition["text"]) if definition["scalable"] else definition["text"]
    metrics = [dict(key=key, label=label, value=round(value * ratio), delta=delta, unit=unit,
                    trend="up" if delta > 0 else "down") for key, label, value, delta, unit in METRICS]
    # Allocate rounding differences so channel contributions always equal total leads.
    weights = [474, 324, 187, 112, 87, 63]
    allocations = [int(weight * ratio) for weight in weights]
    remainder = metrics[3]["value"] - sum(allocations)
    for index in sorted(range(6), key=lambda i: weights[i] * ratio - allocations[i], reverse=True)[:remainder]:
        allocations[index] += 1
    for index, value in enumerate(allocations):
        fields[f"contribution_{index}"] = f"({format_number(value)} Leads)"
    count = min(days, 6)
    offsets = [round(i * (days - 1) / (count - 1)) for i in range(count)] if count > 1 else [0]
    if days == 30:
        offsets = [0, 5, 11, 17, 23, 29]
    dates = [start + timedelta(days=i) for i in offsets]
    trend_shape = [980, 1340, 1840, 2170, 2560, 2960]
    previous_shape = [780, 1070, 1330, 1590, 1840, 2180]
    trends = {}
    for key, factor in [("traffic", 1), ("reach", 7.05), ("leads", .0182), ("spend", 711.05)]:
        trends[key] = {
            "labels": [d.strftime("%d/%m") for d in dates],
            "dates": [d.isoformat() for d in dates],
            "values": [round(trend_shape[min(i, 5)] * factor) for i in range(count)],
            "previous": [round(previous_shape[min(i, 5)] * factor) for i in range(count)],
        }
    return {
        "report_type": "overview", "data_source": "mock",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "period": {"start": start.isoformat(), "end": end.isoformat(), "days": days,
                   "previous_start": (start - timedelta(days=days)).isoformat(),
                   "previous_end": (start - timedelta(days=1)).isoformat()},
        "metrics": metrics, "fields": fields,
        "charts": {"trends": trends, "channel_mix": {"labels": ["Organic Search", "Facebook Ads", "TikTok Ads", "Facebook Content", "Google Maps", "YouTube"], "values": allocations}},
    }
