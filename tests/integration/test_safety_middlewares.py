"""Integration tests for safety middlewares."""

from pathlib import Path
from types import SimpleNamespace

import pytest
from scrapy.http import Request

from webarc.config.loader import load_config
from webarc.crawler.middlewares import (
    BlocklistMiddleware,
    DomainFenceMiddleware,
    WebArcRobotsTxtMiddleware,
)
from webarc.safety.blocklist import reset_blocklist_cache
from webarc.safety.robots import RobotsTxtParser


def test_domain_fence_middleware_allows_and_blocks():
    middleware = DomainFenceMiddleware(allowed_domain="example.com")
    allowed = middleware.process_request(Request("https://example.com/page"), None)
    blocked = middleware.process_request(Request("https://other.com/page"), None)
    assert allowed is None
    assert blocked.status == 403


def test_blocklist_middleware(tmp_path):
    config = load_config()
    config.safety.use_blocklist = True
    blocklist_file = Path(tmp_path) / "blocklist.txt"
    blocklist_file.write_text("0.0.0.0 blocked.com\n")
    config.safety.blocklist_path = str(blocklist_file)
    reset_blocklist_cache()

    middleware = BlocklistMiddleware(config)
    assert middleware.process_request(Request("https://allowed.com/page"), None) is None
    blocked = middleware.process_request(Request("https://blocked.com/page"), None)
    assert blocked.status == 403


def test_robots_middleware(monkeypatch):
    config = load_config()
    config.safety.respect_robots_txt = True

    allow_parser = SimpleNamespace(can_fetch=lambda path: True)
    deny_parser = SimpleNamespace(can_fetch=lambda path: False)

    def fake_parser(domain, user_agent):
        return allow_parser if domain == "example.com" else deny_parser

    monkeypatch.setattr(
        "webarc.crawler.middlewares.RobotsTxtParser",
        fake_parser,
    )

    middleware = WebArcRobotsTxtMiddleware(config)
    assert middleware.process_request(Request("https://example.com/page"), None) is None
    blocked = middleware.process_request(Request("https://blocked.com/page"), None)
    assert blocked.status == 403


def test_robots_middleware_caches_parser(monkeypatch):
    config = load_config()
    config.safety.respect_robots_txt = True
    call_count = {"count": 0}

    def fake_parser(domain, user_agent):
        call_count["count"] += 1
        return SimpleNamespace(can_fetch=lambda path: True)

    monkeypatch.setattr(
        "webarc.crawler.middlewares.RobotsTxtParser",
        fake_parser,
    )

    middleware = WebArcRobotsTxtMiddleware(config)
    middleware.process_request(Request("https://cached.com/page1"), None)
    middleware.process_request(Request("https://cached.com/page2"), None)
    assert call_count["count"] == 1


def test_robots_parser_parses_rules():
    parser = RobotsTxtParser("example.com", user_agent="WebArcBot")
    parser.parse(
        """
        User-agent: WebArcBot
        Disallow: /private
        Allow: /private/allowed
        Crawl-delay: 1
        Sitemap: https://example.com/sitemap.xml
        """
    )
    assert parser.loaded is True
    assert parser.crawl_delay == 1.0
    assert parser.sitemaps == ["https://example.com/sitemap.xml"]
    assert parser.can_fetch("/public") is True
    assert parser.can_fetch("/private") is False

