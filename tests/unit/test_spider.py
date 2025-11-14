"""Unit tests exercising WebArcSpider safety paths."""

from types import SimpleNamespace

import pytest
from scrapy.http import HtmlResponse, Request

from webarc.config.loader import load_config
from webarc.crawler.spider import WebArcSpider
from webarc.utils.url import canonicalize_url


@pytest.fixture
def config():
    return load_config()


@pytest.fixture
def spider(config):
    return WebArcSpider(
        seed_url="https://example.com/root",
        config=config,
        allowed_domain="example.com",
        max_depth=2,
    )


def _dummy_crawler():
    return SimpleNamespace(
        process_response=lambda resp, sp: None,
        manifest_writer=SimpleNamespace(write_graph_entry=lambda entry: None),
    )


def _make_response(url: str, html: str, depth: int = 0) -> HtmlResponse:
    request = Request(url)
    request.meta["depth"] = depth
    return HtmlResponse(
        url=url,
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=request,
    )


def test_spider_version_lock(config):
    spider = WebArcSpider(
        seed_url="https://example.com/appd/25.10.0/root",
        config=config,
        allowed_domain="example.com",
        max_depth=2,
        version_lock="/25.10.0/",
    )
    spider.crawler_instance = _dummy_crawler()

    html = """
    <html><body>
      <a href="https://example.com/appd/25.10.0/keep">Keep</a>
      <a href="https://example.com/appd/24.9.0/skip">Skip</a>
    </body></html>
    """
    response = _make_response("https://example.com/appd/25.10.0/root", html)
    results = list(spider.parse(response))

    assert len(results) == 1
    assert results[0].url.endswith("/keep")
    assert spider.stats["pages_skipped"] == 1


def test_spider_param_explosion_block(spider, monkeypatch):
    spider.config.safety.mode = "enforce"
    spider.crawler_instance = _dummy_crawler()

    monkeypatch.setattr(
        spider.param_detector,
        "check_url",
        lambda url: (True, "too many params"),
    )

    response = _make_response(
        "https://example.com/root",
        '<html><body><a href="https://example.com/page?x=1&y=2">Link</a></body></html>',
    )
    results = list(spider.parse(response))
    assert results == []
    assert spider.stats["pages_skipped"] == 1


def test_spider_random_segment_block(spider, monkeypatch):
    spider.config.safety.mode = "enforce"
    spider.crawler_instance = _dummy_crawler()

    monkeypatch.setattr(
        "webarc.crawler.spider.check_url_for_random_segments",
        lambda url, threshold: (True, ["abcdef"]),
    )

    response = _make_response(
        "https://example.com/root",
        '<html><body><a href="https://example.com/random/abcdef">Link</a></body></html>',
    )
    results = list(spider.parse(response))
    assert results == []
    assert spider.stats["pages_skipped"] == 1


def test_spider_pagination_limit(spider, monkeypatch):
    spider.crawler_instance = _dummy_crawler()
    monkeypatch.setattr(
        spider.pagination_detector,
        "should_follow",
        lambda url: False,
    )

    response = _make_response(
        "https://example.com/root",
        '<html><body><a href="https://example.com/page?page=2">Page 2</a></body></html>',
    )
    results = list(spider.parse(response))
    assert results == []
    assert spider.stats["pages_skipped"] == 1


def test_spider_visited_skip(spider):
    spider.crawler_instance = _dummy_crawler()
    spider.visited_urls.add(canonicalize_url("https://example.com/page1"))

    response = _make_response(
        "https://example.com/root",
        """
        <html><body>
          <a href="https://example.com/page1">Visited</a>
          <a href="https://example.com/page2">New</a>
        </body></html>
        """,
    )
    results = list(spider.parse(response))
    assert len(results) == 1
    assert results[0].url.endswith("page2")

