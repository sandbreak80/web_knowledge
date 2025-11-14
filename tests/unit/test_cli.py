"""Unit-level tests for CLI command helpers."""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import orjson
import pytest
import typer
from click.exceptions import Exit as ClickExit

from webarc.cli.commands import (
    _load_urls,
    crawl,
    fetch,
    plan,
    resume,
    stats,
    validate,
)


def test_plan_command_depth_validation():
    with patch("webarc.cli.commands.console"):
        with pytest.raises(typer.Exit):
            plan(
                seed="https://example.com",
                allow_domain=None,
                allow_prefix=None,
                depth=-5,
                show_rules=False,
                estimate=False,
            )


def test_plan_command_runs(monkeypatch):
    with patch("webarc.cli.commands.console"):
        plan(
            seed="https://example.com",
            allow_domain="example.com",
            allow_prefix=None,
            depth=1,
            show_rules=True,
            estimate=False,
        )


def test_plan_command_with_estimate(monkeypatch):
    """Ensure the estimate flag triggers CrawlPlanner usage."""
    planner = MagicMock()
    planner.plan.return_value = {
        "estimated_pages": 10,
        "sitemap_urls": ["https://example.com/a"],
    }
    with patch("webarc.crawler.planner.CrawlPlanner", return_value=planner):
        with patch("webarc.cli.commands.console"):
            plan(
                seed="https://example.com",
                allow_domain="example.com",
                allow_prefix=None,
                depth=2,
                show_rules=False,
                estimate=True,
            )
    planner.plan.assert_called_once()


def test_crawl_command_error_surface(tmp_path):
    with patch("webarc.cli.commands.console"):
        with patch("webarc.crawler.runner.WebArcCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler.run.side_effect = RuntimeError("Boom")
            mock_crawler_class.return_value = mock_crawler

            with pytest.raises(RuntimeError):
                crawl(
                    seed="https://example.com",
                    allow_domain=None,
                    allow_prefix=None,
                    depth=1,
                    out=str(tmp_path),
                    force_js=False,
                    ignore_robots=False,
                    config_file=None,
                )


def test_fetch_requires_urls(tmp_path):
    with patch("webarc.cli.commands.console"):
        with pytest.raises(typer.Exit):
            fetch(
                url=[],
                urls_file=None,
                out=str(tmp_path),
                config_file=None,
            )


def test_fetch_command_executes(tmp_path):
    urls_file = Path(tmp_path) / "urls.txt"
    urls_file.write_text("https://example.com/one\nhttps://example.com/two\n")

    with patch("webarc.cli.commands.console"):
        with patch("webarc.cli.commands.WebArcFetcher") as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch.return_value = {
                "pages_fetched": 2,
                "pages_extracted": 2,
                "pages_skipped": 0,
                "errors": 0,
            }
            mock_fetcher_class.return_value = mock_fetcher

            fetch(
                url=["https://example.com/root"],
                urls_file=urls_file,
                out=str(tmp_path),
                config_file=None,
            )
            mock_fetcher.fetch.assert_called_once()


def test_resume_missing_state(tmp_path):
    with patch("webarc.cli.commands.console"):
        with pytest.raises(typer.Exit):
            resume(
                state_file=str(tmp_path / "missing.jsonl"),
                out=str(tmp_path),
                config_file=None,
            )


def test_resume_runs(tmp_path):
    state_file = Path(tmp_path) / "resume.jsonl"
    state_file.write_bytes(orjson.dumps({"seed_url": "https://example.com"}))

    with patch("webarc.cli.commands.console"):
        with patch("webarc.crawler.runner.WebArcCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler.run.return_value = {
                "pages_crawled": 1,
                "pages_extracted": 1,
                "pages_skipped": 0,
                "errors": 0,
            }
            mock_crawler_class.return_value = mock_crawler

            resume(
                state_file=str(state_file),
                out=str(tmp_path),
                config_file=None,
            )
            mock_crawler_class.assert_called_once()


def test_stats_missing_manifest(tmp_path):
    with patch("webarc.cli.commands.console"):
        with pytest.raises(typer.Exit):
            stats(output_dir=str(tmp_path))


def test_stats_runs(tmp_path):
    output_dir = Path(tmp_path)
    manifest = output_dir / "manifest.jsonl"
    manifest.write_bytes(
        orjson.dumps(
            {
                "url": "https://example.com/page",
                "file_path": "page.md",
                "word_count": 100,
                "adapter": "GenericAdapter",
                "quality_status": "ok",
            }
        )
    )
    (output_dir / "page.md").write_text("# page")

    with patch("webarc.cli.commands.console"):
        stats(output_dir=str(output_dir))


def test_validate_missing_manifest(tmp_path):
    with patch("webarc.cli.commands.console"):
        with pytest.raises(typer.Exit):
            validate(output_dir=str(tmp_path), check_links=False)


def test_validate_runs(tmp_path):
    output_dir = Path(tmp_path)
    manifest = output_dir / "manifest.jsonl"
    manifest.write_bytes(
        orjson.dumps({"url": "https://example.com", "file_path": "page.md"}) + b"\n"
    )
    (output_dir / "page.md").write_text("# doc")

    with patch("webarc.cli.commands.console"):
        validate(output_dir=str(output_dir), check_links=False)


def test_validate_command_check_links(tmp_path):
    """Validate with link checking exercises graph/broken link path."""
    output_dir = Path(tmp_path)
    manifest = output_dir / "manifest.jsonl"
    page = output_dir / "page.md"
    page.write_text("# Page")
    manifest.write_bytes(
        orjson.dumps(
            {
                "url": "https://example.com/page",
                "file_path": "page.md",
                "word_count": 100,
                "adapter": "GenericAdapter",
                "quality_status": "ok",
            }
        )
    )
    graph = output_dir / "graph.jsonl"
    graph.write_bytes(
        orjson.dumps(
            {
                "source_url": "https://example.com/page",
                "target_url": "https://example.com/missing",
                "link_type": "internal",
            }
        )
    )
    with patch("webarc.cli.commands.console") as mock_console:
        validate(output_dir=str(output_dir), check_links=True)
        assert mock_console.print.call_count > 0


def test_stats_command_with_data(tmp_path):
    """Stats command reads manifest, graph, and errors."""
    output_dir = Path(tmp_path)
    manifest = output_dir / "manifest.jsonl"
    manifest.write_bytes(
        b""
        + orjson.dumps(
            {
                "url": "https://example.com/a",
                "file_path": "a.md",
                "word_count": 100,
                "adapter": "MkDocsAdapter",
                "quality_status": "ok",
                "framework": "mkdocs",
            }
        )
        + b"\n"
        + orjson.dumps(
            {
                "url": "https://example.com/b",
                "file_path": "b.md",
                "word_count": 50,
                "adapter": "NewsAdapter",
                "quality_status": "skipped",
                "framework": "news",
            }
        )
    )
    (output_dir / "a.md").write_text("# A")
    (output_dir / "b.md").write_text("# B")
    graph = output_dir / "graph.jsonl"
    graph.write_bytes(
        orjson.dumps(
            {
                "source_url": "https://example.com/a",
                "target_url": "https://example.com/b",
                "link_type": "internal",
            }
        )
    )
    errors = output_dir / "errors.jsonl"
    errors.write_bytes(
        orjson.dumps(
            {
                "url": "https://example.com/error",
                "error_type": "PROCESSING_ERROR",
            }
        )
    )
    with patch("webarc.cli.commands.console") as mock_console:
        stats(output_dir=str(output_dir))
        printed = " ".join(str(call.args[0]) for call in mock_console.print.call_args_list)
        assert "Adapters Used" in printed
        assert "Error Summary" in printed


def test_load_urls_helper(tmp_path):
    urls_file = Path(tmp_path) / "urls.txt"
    urls_file.write_text(
        """
        https://example.com/one
        # comment
        https://example.com/two
        https://example.com/one
        """.strip()
    )

    urls = _load_urls(["https://example.com/root"], urls_file)
    assert urls == [
        "https://example.com/root",
        "https://example.com/one",
        "https://example.com/two",
    ]


def test_crawl_command_auto_version_lock(tmp_path):
    with patch("webarc.cli.commands.console"):
        with patch("webarc.crawler.runner.WebArcCrawler") as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler.run.return_value = {
                "pages_crawled": 1,
                "pages_extracted": 1,
                "pages_skipped": 0,
                "errors": 0,
            }
            mock_crawler_class.return_value = mock_crawler
            crawl(
                seed="https://example.com/en/app/1.2.3/start",
                allow_domain=None,
                allow_prefix=None,
                depth=1,
                out=str(tmp_path),
                force_js=False,
                ignore_robots=False,
                config_file=None,
                version_lock=None,
            )
            assert mock_crawler_class.call_args.kwargs["version_lock"] == "/1.2.3/"


def test_fetch_command_error_propagation(tmp_path):
    with patch("webarc.cli.commands.console"):
        with patch("webarc.cli.commands.WebArcFetcher") as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch.side_effect = RuntimeError("boom")
            mock_fetcher_class.return_value = mock_fetcher
            with pytest.raises(RuntimeError):
                fetch(
                    url=["https://example.com"],
                    urls_file=None,
                    out=str(tmp_path),
                    config_file=None,
                )

