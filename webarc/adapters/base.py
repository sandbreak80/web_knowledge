"""Base adapter interface for site-specific extraction."""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from bs4 import BeautifulSoup


class SiteAdapter(ABC):
    """
    Base class for site-specific extraction adapters.
    """
    
    @abstractmethod
    def matches(self, url: str, html: str) -> bool:
        """
        Return True if this adapter should handle the page.
        
        Args:
            url: Page URL
            html: HTML content
        
        Returns:
            True if adapter matches
        """
        pass
    
    @abstractmethod
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract and structure content.
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Source URL
        
        Returns:
            Dictionary with:
            - title: str
            - body_html: str (main content only, cleaned)
            - version: str | None (version identifier)
            - lang: str (language code)
            - framework: str (framework name)
            - remove_selectors: List[str] (CSS selectors to remove)
            - metadata: Dict[str, Any] (additional front-matter fields)
        """
        pass
    
    @abstractmethod
    def transform_links(self, source_url: str, links: List[str]) -> List[str]:
        """
        Transform links to Obsidian format.
        
        Args:
            source_url: Source page URL
            links: List of link URLs
        
        Returns:
            List of transformed links
        """
        pass
