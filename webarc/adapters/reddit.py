"""Reddit adapter that consumes the public JSON API."""

from __future__ import annotations

from html import unescape
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from webarc.adapters.base import SiteAdapter
from webarc.config.schema import WebArcConfig


class RedditAdapter(SiteAdapter):
    """
    Adapter for Reddit pages using the public `.json` endpoints.

    This adapter avoids fragile HTML scraping and instead leverages Reddit's
    JSON representations of listings and comment threads.
    """

    def __init__(self, config: WebArcConfig):
        self.config = config
        reddit_config = getattr(config.adapters, "reddit", None)
        self.enabled = True
        self.user_agent = config.crawler.user_agent
        self.use_json_api = True
        self.request_timeout = 15

        if reddit_config is not None:
            self.enabled = getattr(reddit_config, "enabled", True)
            if getattr(reddit_config, "user_agent", None):
                self.user_agent = reddit_config.user_agent
            self.use_json_api = getattr(reddit_config, "use_json_api", True)
            self.request_timeout = getattr(reddit_config, "request_timeout", 15)

    def matches(self, url: str, html: str) -> bool:
        """
        Detect Reddit domains (`reddit.com`, `new.reddit.com`, `redd.it`).
        """
        if not self.enabled:
            return False
        domain = urlparse(url).netloc.lower()
        if domain.endswith("reddit.com") or domain.endswith("redd.it"):
            return True
        return False

    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Convert Reddit JSON responses into HTML content.
        """
        if not self.use_json_api:
            return self._html_fallback(soup, url)

        try:
            payload = self._fetch_json(url)
        except Exception as exc:  # pragma: no cover - defensive
            return {
                "title": "Reddit",
                "body_html": f"<p>Failed to load Reddit JSON: {exc}</p>",
                "version": None,
                "lang": "en",
                "framework": "reddit-json",
                "remove_selectors": [],
                "metadata": {
                    "extracted_with": "RedditAdapter",
                    "error": str(exc),
                },
            }

        content = self._render_payload(url, payload)

        # Attempt to infer title from rendered content
        title = content.get("title") or "Reddit"
        body_html = content.get("body_html", "<p>No content</p>")

        return {
            "title": title,
            "body_html": body_html,
            "version": None,
            "lang": "en",
            "framework": "reddit-json",
            "remove_selectors": [],
            "metadata": {
                "extracted_with": "RedditAdapter",
                **content.get("metadata", {}),
            },
        }

    def transform_links(self, source_url: str, links: List[str]) -> List[str]:
        """
        Normalize Reddit links to absolute ``https://www.reddit.com`` URLs.
        """
        normalized = []
        for link in links:
            if link.startswith("/"):
                normalized.append(f"https://www.reddit.com{link}")
            else:
                normalized.append(link)
        return normalized

    # --------------------------------------------------------------------- #
    # Internal helpers
    # --------------------------------------------------------------------- #

    def _fetch_json(self, url: str) -> Any:
        """
        Fetch the Reddit JSON representation for ``url``.
        """
        json_url = self._to_json_url(url)
        headers = {"User-Agent": self.user_agent}
        response = requests.get(json_url, headers=headers, timeout=self.request_timeout)
        response.raise_for_status()
        return response.json()

    def _to_json_url(self, url: str) -> str:
        """
        Append ``.json`` to Reddit URLs while preserving query parameters.
        """
        parsed = urlparse(url)
        path = parsed.path
        if not path.endswith(".json"):
            path = path.rstrip("/") + ".json"
        new_url = parsed._replace(path=path).geturl()
        return new_url

    def _render_payload(self, url: str, payload: Any) -> Dict[str, Any]:
        """
        Convert Reddit JSON payload into HTML markup.
        """
        if isinstance(payload, list) and len(payload) >= 2:
            return self._render_comments(payload)
        if isinstance(payload, dict):
            return self._render_listing(payload)
        return {"title": "Reddit", "body_html": "<p>No content</p>"}

    def _render_listing(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Render subreddit listing JSON.
        """
        listing = data.get("data", {})
        children = listing.get("children", [])
        title = listing.get("title") or listing.get("display_name_prefixed") or "Reddit"
        description = listing.get("public_description") or ""

        parts: List[str] = []
        if description:
            parts.append(f"<p>{self._escape(description)}</p>")

        for child in children:
            post = child.get("data", {})
            parts.append(self._render_post_card(post))

        if not parts:
            parts.append("<p>No posts found.</p>")

        return {
            "title": title,
            "body_html": "\n".join(parts),
            "metadata": {"reddit_type": "listing", "subreddit": listing.get("display_name")},
        }

    def _render_comments(self, payload: List[Any]) -> Dict[str, Any]:
        """
        Render comment thread JSON payload.
        """
        post_info = payload[0].get("data", {}).get("children", [])
        if post_info:
            post_data = post_info[0].get("data", {})
        else:
            post_data = {}

        comments_listing = payload[1].get("data", {}).get("children", [])
        parts: List[str] = [self._render_post_card(post_data, include_selftext=True)]
        parts.append("<h2>Top Comments</h2>")

        if comments_listing:
            for comment in comments_listing:
                comment_data = comment.get("data", {})
                if comment.get("kind") != "t1":
                    continue
                parts.append(self._render_comment(comment_data, depth=0))
        else:
            parts.append("<p>No comments available.</p>")

        title = post_data.get("title") or "Reddit Discussion"

        return {
            "title": title,
            "body_html": "\n".join(parts),
            "metadata": {
                "reddit_type": "comments",
                "permalink": post_data.get("permalink"),
            },
        }

    def _render_post_card(self, post: Dict[str, Any], include_selftext: bool = False) -> str:
        """
        Render a single Reddit post into HTML.
        """
        permalink = post.get("permalink") or ""
        url = f"https://www.reddit.com{permalink}" if permalink else post.get("url_overridden_by_dest", "#")
        title = self._escape(post.get("title", "Untitled"))
        author = post.get("author")
        score = post.get("score")
        flair = post.get("link_flair_text")

        header_parts = [f'<h2><a href="{url}">{title}</a></h2>']
        meta_bits = []
        if author:
            meta_bits.append(f"u/{self._escape(author)}")
        if flair:
            meta_bits.append(self._escape(flair))
        if score is not None:
            meta_bits.append(f"{score} points")
        if meta_bits:
            header_parts.append(f"<p><em>{' • '.join(meta_bits)}</em></p>")

        body_parts = header_parts
        selftext_html = post.get("selftext_html")
        if include_selftext and selftext_html:
            body_parts.append(f'<div class="reddit-selftext">{unescape(selftext_html)}</div>')

        return "\n".join(body_parts)

    def _render_comment(self, comment: Dict[str, Any], depth: int) -> str:
        """
        Render a Reddit comment and nested replies (limited depth to keep output manageable).
        """
        author = comment.get("author") or "[deleted]"
        body_html = comment.get("body_html")
        if not body_html:
            return ""

        score = comment.get("score")
        header = f"<strong>{self._escape(author)}</strong>"
        if score is not None:
            header += f" ({score} points)"

        parts = [
            '<div class="reddit-comment" style="margin-left: {}em">'.format(depth * 1.5),
            f"<p>{header}</p>",
            f'<div class="reddit-comment-body">{unescape(body_html)}</div>',
        ]

        if depth < 2:
            replies = comment.get("replies")
            if isinstance(replies, dict):
                children = replies.get("data", {}).get("children", [])
                for child in children:
                    if child.get("kind") != "t1":
                        continue
                    parts.append(self._render_comment(child.get("data", {}), depth + 1))

        parts.append("</div>")
        return "\n".join(parts)

    def _html_fallback(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Fallback extraction if JSON API usage is disabled.
        """
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else "Reddit"
        body = soup.find("body")
        body_html = str(body) if body else "<p>No content</p>"
        return {
            "title": title,
            "body_html": body_html,
            "version": None,
            "lang": "en",
            "framework": "reddit-html",
            "remove_selectors": [],
            "metadata": {
                "extracted_with": "RedditAdapter",
                "mode": "html-fallback",
            },
        }

    @staticmethod
    def _escape(value: Optional[str]) -> str:
        if not value:
            return ""
        return unescape(value).strip()

