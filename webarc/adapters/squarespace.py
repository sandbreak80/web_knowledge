"""Squarespace adapter for Squarespace-hosted sites."""

from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from webarc.adapters.base import SiteAdapter
from webarc.config.schema import WebArcConfig


class SquarespaceAdapter(SiteAdapter):
    """
    Adapter for Squarespace-powered sites.

    Squarespace uses heavily nested div structures with dynamic class names
    prefixed by ``sqs-``. The content is typically rendered client-side, so
    Playwright rendering is recommended before running this adapter.
    """

    def __init__(self, config: WebArcConfig):
        self.config = config
        adapter_config = getattr(config.adapters, "squarespace", None)

        default_content_selectors = [
            'main',
            '[data-content-field="main-content"]',
            '.sqs-layout',
            '.sqs-layout[data-type="page-section"]',
            '.sqs-layout[data-type="page"]',
            '.Site-inner',
            '.Index-page-content',
            '.Index-page',
            '.page-section',
            '.Main',
        ]
        default_remove_selectors = [
            'header',
            'nav',
            'footer',
            '.Header',
            '.Footer',
            '.SiteHeader',
            '.SiteFooter',
            '.sqs-announcement-bar',
            '.sqs-popup-overlay',
            '.sqs-cookie-banner',
            '.sqs-search-ui',
            '.sqs-cart-dropzone',
            '.sqs-block-social-links',
            '.sqs-share-button-wrapper',
            '.sqs-audio-block',
        ]

        if adapter_config is not None:
            self.enabled = getattr(adapter_config, "enabled", True)
        else:
            self.enabled = True

        if adapter_config and getattr(adapter_config, "enabled", True):
            config_selectors = getattr(adapter_config, "content_selectors", []) or []
            config_remove = getattr(adapter_config, "remove_selectors", []) or []
        else:
            config_selectors = []
            config_remove = []

        # Preserve order while ensuring uniqueness
        self.content_selectors = list(dict.fromkeys(config_selectors + default_content_selectors))
        self.remove_selectors = list(dict.fromkeys(config_remove + default_remove_selectors))

    def matches(self, url: str, html: str) -> bool:
        """
        Detect Squarespace pages via domain hints and structural class names.
        """
        if not self.enabled:
            return False

        lower_html = html.lower()
        if "static.squarespace.com" in lower_html:
            return True
        if "sqs-" in lower_html:
            soup = BeautifulSoup(html, "lxml")
            if soup.find(class_=lambda value: value and "sqs-" in value):
                return True
        if "squarespace" in url.lower():
            return True
        soup = BeautifulSoup(html, "lxml")
        generator = soup.find("meta", attrs={"name": "generator"})
        if generator and "squarespace" in generator.get("content", "").lower():
            return True
        return False

    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract structured content from Squarespace layouts.
        """
        # Determine title
        title: Optional[str] = None
        main_heading = soup.find("h1")
        if main_heading:
            title = main_heading.get_text(strip=True)
        if not title:
            title_tag = soup.find("title")
            title = title_tag.get_text(strip=True) if title_tag else "Untitled"

        # Locate main content container
        content_node = self._find_primary_container(soup)
        content_clone = BeautifulSoup(str(content_node), "lxml") if content_node else soup

        # Remove navigation / boilerplate elements
        for selector in self.remove_selectors:
            for element in content_clone.select(selector):
                element.decompose()

        # Remove empty blocks (common for spacer/line blocks)
        for block in content_clone.find_all(class_=lambda value: value and "sqs-block-code" in value):
            if not block.get_text(strip=True):
                block.decompose()

        for tag in content_clone.find_all(['script', 'style']):
            tag.decompose()

        html_tag = soup.find("html")
        lang = html_tag.get("lang", "en") if html_tag else "en"

        return {
            "title": title,
            "body_html": str(content_clone),
            "version": None,
            "lang": lang,
            "framework": "squarespace",
            "remove_selectors": self.remove_selectors,
            "metadata": {
                "extracted_with": "SquarespaceAdapter"
            },
        }

    def transform_links(self, source_url: str, links: List[str]) -> List[str]:
        """
        Squarespace links can remain unchanged; relative URLs are already suitable.
        """
        return links

    def _find_primary_container(self, soup: BeautifulSoup):
        """
        Identify the best candidate for primary page content.
        """
        for selector in self.content_selectors:
            node = soup.select_one(selector)
            if node and node.get_text(strip=True):
                return node

        # Fallback to body if no structured container is found
        return soup.body

