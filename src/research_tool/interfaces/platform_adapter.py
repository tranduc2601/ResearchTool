"""Abstract interface for platform-specific UI hints.

PlatformAdapters are OPTIONAL helpers that can improve state detection
by providing platform-specific knowledge (e.g. URL patterns → page type).
The core functions correctly even when no adapter is registered.

Implementations: research_tool.implementations.platform
"""

from abc import ABC, abstractmethod

from research_tool.domain import PageType


class PlatformAdapter(ABC):
    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Canonical platform identifier (e.g. 'shopee', 'tiktok', 'facebook')."""
        ...

    @abstractmethod
    def identify_page_type(self, url: str, title: str) -> PageType | None:
        """
        Guess the page type from URL + title. Returns None if unsure.
        Core will use VisionProvider as the primary method; this is a fast hint.
        """
        ...

    @abstractmethod
    def extract_entity_id_from_url(self, url: str) -> str | None:
        """
        Extract a platform-native entity ID from a URL.
        e.g. Shopee product ID from https://shopee.vn/.../1234567890
        Returns None if the URL doesn't match this platform's pattern.
        """
        ...
