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
FACEBOOK_CONTENT_FRAGMENTS = (
    "kpis",
    "formats",
    "topics",
    "posts",
    "engagement",
    "reach_mix",
    "insights",
)


def video_fragments(video: Mapping[str, Any]) -> dict[str, str]:
    channel = video['channel']
    return {
        'kpis': _templates.get_template('pages/video/partials/kpis.html').render(video=video),
        'table': _templates.get_template(f'pages/{channel}/partials/table.html').render(video=video),
        'funnel': _templates.get_template('pages/video/partials/funnel.html').render(video=video),
        'videos': _templates.get_template('pages/tiktok/partials/videos.html').render(video=video) if channel == 'tiktok' else '',
    }

def facebook_ads_fragments(ads: Mapping[str, Any]) -> dict[str, str]:
    """Render each dynamic Facebook Ads section for the page and API response."""
    return {
        name: _templates.get_template(f"pages/facebook_ads/partials/{name}.html").render(ads=ads)
        for name in FB_FRAGMENTS
    }

def facebook_content_fragments(
    fb_content: Mapping[str, Any],
) -> dict[str, str]:

    return {
        name: (
            _templates
            .get_template(
                "pages/"
                "facebook_content/"
                "partials/"
                f"{name}.html"
            )
            .render(
                fb_content=fb_content
            )
        )

        for name
        in FACEBOOK_CONTENT_FRAGMENTS
    }
