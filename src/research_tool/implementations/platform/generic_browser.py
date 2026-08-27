"""Generic browser PlatformAdapter — minimal URL-pattern hints."""

from __future__ import annotations

from research_tool.domain import PageType
from research_tool.interfaces import PlatformAdapter


class GenericBrowserAdapter(PlatformAdapter):
    """
    Provides minimal URL-based page type hints for generic browser sessions.
    Recognizes common URL patterns without platform-specific knowledge.
    """

    @property
    def platform_name(self) -> str:
        return "generic_browser"

    def identify_page_type(self, url: str, title: str) -> PageType | None:
        url_lower = url.lower()
        if not url or url == "about:blank":
            return PageType.UNKNOWN
        # Very coarse heuristics — real adapters add platform-specific logic
        if any(q in url_lower for q in ["search?", "q=", "query=", "/search/"]):
            return PageType.SEARCH_RESULT
        return None  # Unknown — let VisionProvider decide

    def extract_entity_id_from_url(self, url: str) -> str | None:
        # No generic extraction — platform-specific adapters handle this
        return None
