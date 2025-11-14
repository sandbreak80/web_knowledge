"""Unit tests for the crawler runner module."""

from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from webarc.config.loader import load_config
from webarc.crawler.runner import (
    WebArcCrawler,
    WebArcFetcher,
    _extract_sitemap_urls,
)


@pytest.fixture
def config():
    """Return a fresh configuration object for each test."""
    cfg = load_config()
    # Lower extraction thresholds to make synthetic HTML pass quality checks.
    cfg.extraction.min_content_density = 0
    cfg.extraction.min_content_length = 0
    cfg.extraction.min_word_count = 1
    cfg.extraction.require_heading = False
    return cfg


def test_crawler_run_invokes_scrapy(monkeypatch, tmp_path, config):
    """Ensure the runner wires CrawlerProcess correctly."""
    fake_process = MagicMock()
    monkeypatch.setattr(
        "webarc.crawler.runner.CrawlerProcess",
        MagicMock(return_value=fake_process),
    )
    crawler = WebArcCrawler(
        seed_url="https://example.com/start",
        config=config,
        output_dir=Path(tmp_path),
        max_depth=1,
    )
    crawler.extra_seed_urls = ["https://example.com/extra"]

    stats = crawler.run()

    fake_process.crawl.assert_called_once()
    kwargs = fake_process.crawl.call_args.kwargs
    assert kwargs["seed_url"] == "https://example.com/start"
    assert kwargs["extra_seed_urls"] == ["https://example.com/extra"]
    fake_process.start.assert_called_once()
    # Stats object is returned unchanged at the moment.
    assert stats == crawler.stats


def test_process_response_success(tmp_path, config):
    """pipeline success increments counters and checkpoints state."""
    crawler = WebArcCrawler(
        seed_url="https://example.com/start",
        config=config,
        output_dir=Path(tmp_path),
    )
    crawler.pipeline.process = MagicMock(
        return_value={
            "success": True,
            "file_path": Path(tmp_path) / "file.md",
            "quality": MagicMock(),
            "metadata": {"title": "OK"},
        }
    )
    crawler.state_manager.maybe_checkpoint = MagicMock()

    response = SimpleNamespace(
        url="https://example.com/page",
        text="<html><body><p>content</p></body></html>",
        status=200,
    )
    spider = SimpleNamespace(visited_urls={"https://example.com/page"})

    crawler.process_response(response, spider)

    assert crawler.stats["pages_crawled"] == 1
    assert crawler.stats["pages_extracted"] == 1
    crawler.state_manager.maybe_checkpoint.assert_called_once()


def test_process_response_skip(tmp_path, config):
    """pipeline returning success=False counts as skipped."""
    crawler = WebArcCrawler(
        seed_url="https://example.com/start",
        config=config,
        output_dir=Path(tmp_path),
    )
    crawler.pipeline.process = MagicMock(
        return_value={"success": False, "reason": "too short"}
    )

    response = SimpleNamespace(
        url="https://example.com/page",
        text="<html></html>",
        status=200,
    )
    spider = SimpleNamespace(visited_urls=set())

    crawler.process_response(response, spider)

    assert crawler.stats["pages_crawled"] == 1
    assert crawler.stats["pages_skipped"] == 1


def test_process_response_error_path(tmp_path, config, caplog):
    """pipeline exceptions are captured and recorded as errors."""
    crawler = WebArcCrawler(
        seed_url="https://example.com/start",
        config=config,
        output_dir=Path(tmp_path),
    )
    def boom(url, html, status):
        raise RuntimeError("boom")

    crawler.pipeline.process = boom
    crawler.manifest_writer.write_error_entry = MagicMock()

    response = SimpleNamespace(
        url="https://example.com/page",
        text="<html></html>",
        status=500,
    )
    spider = SimpleNamespace(visited_urls=set())

    with caplog.at_level("ERROR"):
        crawler.process_response(response, spider)

    assert crawler.stats["errors"] == 1
    crawler.manifest_writer.write_error_entry.assert_called_once()


def test_load_version_seed_urls_success(monkeypatch, tmp_path, config):
    """_load_version_seed_urls parses sitemap index and returns filtered URLs."""
    index_xml = """
    <sitemapindex>
        <sitemap>
            <loc>https://docs.example.com/en/appdynamics-saas/sitemap.xml</loc>
        </sitemap>
    </sitemapindex>
    """.strip()

    detail_xml = """
    <urlset>
        <url><loc>https://docs.example.com/en/appdynamics-saas/application-performance-monitoring/25.10.0/page</loc></url>
        <url><loc>https://docs.example.com/en/appdynamics-saas/application-performance-monitoring/25.9.0/other</loc></url>
    </urlset>
    """.strip()

    class FakeResponse:
        def __init__(self, text, status=200):
            self.text = text
            self.status_code = status

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError("bad status")

    def fake_get(url, headers=None, timeout=None):
        if url.endswith("sitemap.xml") and "en/appdynamics-saas" not in url:
            return FakeResponse(index_xml)
        return FakeResponse(detail_xml)

    monkeypatch.setattr("webarc.crawler.runner.requests", SimpleNamespace(get=fake_get))

    crawler = WebArcCrawler(
        seed_url="https://docs.example.com/en/appdynamics-saas/application-performance-monitoring/25.10.0/root",
        config=config,
        output_dir=Path(tmp_path),
        version_lock="/25.10.0/",
    )

    assert crawler.extra_seed_urls == [
        "https://docs.example.com/en/appdynamics-saas/application-performance-monitoring/25.10.0/page"
    ]


def test_load_version_seed_urls_requests_missing(monkeypatch, tmp_path, config):
    """Requests import missing should short-circuit to an empty list."""
    monkeypatch.setattr("webarc.crawler.runner.requests", None)
    crawler = WebArcCrawler(
        seed_url="https://docs.example.com/en/appdynamics-saas/application-performance-monitoring/25.10.0/root",
        config=config,
        output_dir=Path(tmp_path),
        version_lock="/25.10.0/",
    )
    assert crawler.extra_seed_urls == []


def test_extract_sitemap_urls_parsing():
    """XML helper handles valid and invalid documents."""
    xml = """
    <urlset>
        <url><loc>https://example.com/a</loc></url>
        <url><loc>https://example.com/b</loc></url>
    </urlset>
    """
    assert _extract_sitemap_urls(xml) == [
        "https://example.com/a",
        "https://example.com/b",
    ]
    # Malformed XML returns an empty list
    assert _extract_sitemap_urls("<urlset><url></urlset>") == []


def test_fetcher_fetch_success(monkeypatch, tmp_path, config):
    """WebArcFetcher processes 200 responses through the pipeline."""
    fetcher = WebArcFetcher(config=config, output_dir=Path(tmp_path))
    fetcher.pipeline.process = MagicMock(return_value={"success": True})

    class DummyResponse:
        status_code = 200
        text = "<html></html>"

    monkeypatch.setattr(
        "webarc.crawler.runner.requests",
        SimpleNamespace(get=MagicMock(return_value=DummyResponse())),
    )

    stats = fetcher.fetch(["https://example.com"])
    assert stats["pages_fetched"] == 1
    assert stats["pages_extracted"] == 1
    fetcher.pipeline.process.assert_called_once()


def test_fetcher_handles_errors(monkeypatch, tmp_path, config, caplog):
    """Errors and non-200 responses increment correct counters."""
    fetcher = WebArcFetcher(config=config, output_dir=Path(tmp_path))
    fetcher.pipeline.process = MagicMock(return_value={"success": False, "reason": "bad"})

    class ErrorResponse:
        status_code = 500
        text = "error"

    # First URL raises exception, second returns 500, third returns success but pipeline false
    def fake_get(url, timeout, headers):
        if "boom" in url:
            raise RuntimeError("boom")
        if "fail" in url:
            return ErrorResponse()
        return SimpleNamespace(status_code=200, text="<html></html>")

    monkeypatch.setattr(
        "webarc.crawler.runner.requests",
        SimpleNamespace(get=fake_get),
    )

    with caplog.at_level("ERROR"):
        stats = fetcher.fetch(
            ["https://example.com/boom", "https://example.com/fail", "https://example.com/skip"]
        )

    assert stats["errors"] == 1
    assert stats["pages_skipped"] == 2  # one HTTP 500, one pipeline skip
    assert "Failed to fetch" in caplog.text

