"""Shared HTML fragments used by the Facebook Ads page and JSON endpoint."""
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader, select_autoescape

_templates = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parents[1] / "templates"),
    autoescape=select_autoescape(["html"]),
)
FB_FRAGMENTS: tuple[str, ...] = (
    "kpis",
    "campaigns",
    "funnel",
    "audience",
    "creatives",
    "insights",
)


def facebook_ads_fragments(ads: Mapping[str, Any]) -> dict[str, str]:
    """Render each dynamic Facebook Ads section for the page and API response."""
    return {
        name: _templates.get_template(f"facebook_ads/{name}.html").render(ads=ads)
        for name in FB_FRAGMENTS
    }
