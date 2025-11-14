"""Unit tests for crawler middlewares."""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from scrapy.http import Request

from webarc.config.loader import load_config
from webarc.crawler.middlewares import (
    BlocklistMiddleware,
    DomainFenceMiddleware,
    WebArcRobotsTxtMiddleware,
)


def test_domain_fence_allows_and_blocks():
    middleware = DomainFenceMiddleware(allowed_domain="example.com", allowed_prefix="/docs")

    allowed_request = Request("https://example.com/docs/page")
    blocked_request = Request("https://other.com/docs/page")
    blocked_prefix = Request("https://example.com/blog/page")

    assert middleware.process_request(allowed_request, None) is None
    assert middleware.process_request(blocked_request, None).status == 403
    assert middleware.process_request(blocked_prefix, None).status == 403


def test_robots_txt_middleware(monkeypatch):
    config = load_config()
    config.safety.respect_robots_txt = True

    class DummyParser:
        def __init__(self, domain, user_agent):
            self.domain = domain
            self.user_agent = user_agent
            self.allowed = False

        def can_fetch(self, path: str) -> bool:
            return self.allowed

    def fake_parser(domain, user_agent):
        parser = DummyParser(domain, user_agent)
        return parser

    monkeypatch.setattr(
        "webarc.crawler.middlewares.RobotsTxtParser",
        fake_parser,
    )

    middleware = WebArcRobotsTxtMiddleware(config)

    request = Request("https://example.com/private")
    # First call hits parser.allowed False -> blocked
    response = middleware.process_request(request, None)
    assert response.status == 403

    # Cache the parser and allow access next time
    middleware.robots_cache["example.com"].allowed = True
    response = middleware.process_request(Request("https://example.com/allowed"), None)
    assert response is None

    # When respect_robots_txt disabled, skip checks
    config.safety.respect_robots_txt = False
    assert middleware.process_request(Request("https://example.com/any"), None) is None


def test_blocklist_middleware(monkeypatch):
    config = load_config()
    config.safety.use_blocklist = True

    def fake_check(domain, _path):
        return domain == "blocked.com"

    monkeypatch.setattr(
        "webarc.crawler.middlewares.check_blocklist",
        fake_check,
    )

    middleware = BlocklistMiddleware(config)

    allowed = middleware.process_request(Request("https://allowed.com/page"), None)
    blocked = middleware.process_request(Request("https://blocked.com/page"), None)

    assert allowed is None
    assert blocked.status == 403

    config.safety.use_blocklist = False
    assert middleware.process_request(Request("https://blocked.com/page"), None) is None

