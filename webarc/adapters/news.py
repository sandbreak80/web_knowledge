"""News adapter for article-oriented sites."""

from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from webarc.adapters.base import SiteAdapter
from webarc.config.schema import WebArcConfig


class NewsAdapter(SiteAdapter):
    """
    Adapter aimed at traditional news/article layouts.

    Detection relies on the presence of ``<article>`` tags, Open Graph metadata,
    or schema.org ``NewsArticle``/``Article`` annotations.
    """

    def __init__(self, config: WebArcConfig):
        self.config = config
        news_config = getattr(config.adapters, "news", None)
        if news_config is not None:
            self.enabled = getattr(news_config, "enabled", True)
            content_selectors = getattr(news_config, "content_selectors", []) or []
            remove_selectors = getattr(news_config, "remove_selectors", []) or []
        else:
            self.enabled = True
            content_selectors = []
            remove_selectors = []

        default_content_selectors = [
            "main",
            'main[role="main"]',
            ".article__content",
            ".story-body",
            ".Article-content",
            "article",
            'article > section',
        ]
        default_remove_selectors = [
            "body > header",
            "body > footer",
            ".advertisement",
            ".ad-container",
            ".share-tools",
            ".social-share",
            ".article-sidebar",
            ".inset-media",
        ]

        ordered_content = default_content_selectors + content_selectors
        self.content_selectors = list(dict.fromkeys(ordered_content))
        ordered_remove = default_remove_selectors + remove_selectors
        self.remove_selectors = list(dict.fromkeys(ordered_remove))

    def matches(self, url: str, html: str) -> bool:
        if not self.enabled:
            return False
        soup = BeautifulSoup(html, "lxml")
        if soup.find("article"):
            return True
        og_type = soup.find("meta", property="og:type")
        if og_type and og_type.get("content", "").lower() in {"article", "news", "article:news"}:
            return True
        ld_json_blocks = soup.find_all("script", type="application/ld+json")
        for block in ld_json_blocks:
            text = block.get_text(strip=True)
            if '"@type":"' in text:
                lowered = text.lower()
                if '"@type":"newsarticle"' in lowered or '"@type":"article"' in lowered:
                    return True
        return False

    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        title = self._extract_title(soup)
        content_node = self._locate_content_node(soup)
        content_clone = BeautifulSoup(str(content_node), "lxml") if content_node else soup

        for selector in self.remove_selectors:
            for node in content_clone.select(selector):
                node.decompose()

        for tag in content_clone.find_all(["script", "style", "noscript"]):
            tag.decompose()

        lang = self._detect_language(soup)

        return {
            "title": title,
            "body_html": str(content_clone),
            "version": None,
            "lang": lang,
            "framework": "news",
            "remove_selectors": self.remove_selectors,
            "metadata": {
                "extracted_with": "NewsAdapter",
            },
        }

    def transform_links(self, source_url: str, links: List[str]) -> List[str]:
        normalized: List[str] = []
        for link in links:
            if link.startswith("//"):
                normalized.append(f"https:{link}")
            elif link.startswith("/"):
                normalized.append(urljoin(source_url, link))
            else:
                normalized.append(link)
        return normalized

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> str:
        title_tag = soup.find("meta", property="og:title") or soup.find("title")
        if title_tag:
            content = title_tag.get("content")
            if content:
                return content.strip()
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        return "Untitled Article"

    def _locate_content_node(self, soup: BeautifulSoup):
        for selector in self.content_selectors:
            node = soup.select_one(selector)
            if node and node.get_text(strip=True):
                return node
        body = soup.find("body")
        return body

    @staticmethod
    def _detect_language(soup: BeautifulSoup) -> str:
        html_tag = soup.find("html")
        if html_tag and html_tag.get("lang"):
            return html_tag.get("lang")
        meta_lang = soup.find("meta", attrs={"http-equiv": "content-language"})
        if meta_lang and meta_lang.get("content"):
            return meta_lang.get("content").split(",")[0]
        return "en"

