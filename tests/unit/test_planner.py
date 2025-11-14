"""Unit tests for the crawl planner."""

from pathlib import Path
from types import SimpleNamespace

import pytest

from webarc.config.loader import load_config
from webarc.crawler.planner import CrawlPlanner


@pytest.fixture
def config():
    cfg = load_config()
    return cfg


def test_planner_seed_validation_failure(config):
    """Planner reports an error when seed violates domain restriction."""
    planner = CrawlPlanner(
        seed_url="https://other.com/page",
        config=config,
        allowed_domain="example.com",
    )
    plan = planner.plan()
    assert plan["error"].startswith("Seed URL validation failed")


def test_planner_discovers_sitemap(monkeypatch, config):
    """Planner fetches sitemap URLs via robots.txt hint."""

    class DummyResponse:
        def __init__(self, text="", content=None, status=200):
            self.text = text
            self.content = content if content is not None else text.encode("utf-8")
            self.status_code = status

    def fake_get(url, timeout=10, allow_redirects=True):
        if url.endswith("/robots.txt"):
            return DummyResponse("Sitemap: https://example.com/sitemap.xml")
        if "sitemap.xml" in url:
            xml = """
            <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
                <url><loc>https://example.com/a</loc></url>
                <url><loc>https://example.com/b</loc></url>
            </urlset>
            """.strip()
            return DummyResponse(content=xml.encode("utf-8"))
        return DummyResponse(status=404)

    monkeypatch.setattr("requests.get", fake_get, raising=True)

    planner = CrawlPlanner(
        seed_url="https://example.com/index",
        config=config,
    )

    plan = planner.plan()

    assert plan["estimated_pages"] == 2
    assert plan["sitemap_urls"] == [
        "https://example.com/a",
        "https://example.com/b",
    ]


def test_planner_parse_sitemap_errors(monkeypatch, config, caplog):
    """_parse_sitemap swallows exceptions and returns an empty list."""

    def fake_get(url, timeout=10, allow_redirects=True):
        raise RuntimeError("network down")

    monkeypatch.setattr("requests.get", fake_get, raising=True)

    planner = CrawlPlanner(
        seed_url="https://example.com",
        config=config,
    )

    with caplog.at_level("DEBUG"):
        urls = planner._parse_sitemap("https://example.com/sitemap.xml")

    assert urls == []
    assert "network down" in caplog.text

