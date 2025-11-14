"""Integration tests for CLI commands."""

import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
import orjson
import typer
from click.exceptions import Exit as ClickExit

from webarc.cli.commands import (
    plan,
    crawl,
    resume,
    validate,
    stats,
    _load_urls,
)


def test_plan_command_basic():
    """Test plan command basic functionality."""
    # Mock console.print to capture output
    with patch('webarc.cli.commands.console') as mock_console:
        plan(
            seed='https://example.com',
            allow_domain=None,
            allow_prefix=None,
            depth=2,
            show_rules=False,
            estimate=False,
        )
        
        # Verify console.print was called
        assert mock_console.print.called


def test_plan_command_with_estimate():
    """Test plan command with estimate flag."""
    with patch('webarc.cli.commands.console'):
        with patch('webarc.crawler.planner.CrawlPlanner.plan') as mock_plan:
            mock_plan.return_value = {
                'estimated_pages': 10,
                'sitemap_urls': ['https://example.com/page1'],
            }
            
            plan(
                seed='https://example.com',
                allow_domain=None,
                allow_prefix=None,
                depth=2,
                show_rules=False,
                estimate=True,
            )
            
            assert mock_plan.called


def test_plan_command_invalid_depth(monkeypatch):
    """Ensure invalid depth raises TyperExit."""
    with patch('webarc.cli.commands.console'):
        with pytest.raises(typer.Exit):
            plan(
                seed='https://example.com',
                allow_domain=None,
                allow_prefix=None,
                depth=-1,
                show_rules=False,
                estimate=False,
            )


def test_validate_command():
    """Test validate command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Create manifest file
        manifest_file = output_dir / 'manifest.jsonl'
        with open(manifest_file, 'wb') as f:
            entry = {
                'url': 'https://example.com/page',
                'file_path': 'page.md',
            }
            f.write(orjson.dumps(entry) + b'\n')
        
        # Create the referenced file
        (output_dir / 'page.md').write_text('# Test Page')
        
        with patch('webarc.cli.commands.console') as mock_console:
            try:
                validate(
                    output_dir=str(output_dir),
                    check_links=False,
                )
            except SystemExit:
                pass  # Expected if validation fails
            
            assert mock_console.print.called


def test_validate_command_missing_manifest(tmp_path):
    """Validation exits cleanly when manifest missing."""
    with patch('webarc.cli.commands.console') as mock_console:
        with pytest.raises(typer.Exit):
            validate(
                output_dir=str(tmp_path),
                check_links=False,
            )
        mock_console.print.assert_called()


def test_validate_command_missing_files():
    """Test validate command with missing files."""
    import typer
    from click.exceptions import Exit as ClickExit
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Create manifest file pointing to non-existent file
        manifest_file = output_dir / 'manifest.jsonl'
        with open(manifest_file, 'wb') as f:
            entry = {
                'url': 'https://example.com/page',
                'file_path': 'missing.md',
            }
            f.write(orjson.dumps(entry) + b'\n')
        
        with patch('webarc.cli.commands.console') as mock_console:
            try:
                validate(
                    output_dir=str(output_dir),
                    check_links=False,
                )
            except (SystemExit, typer.Exit, ClickExit):
                pass  # Expected exit code 1
            
            assert mock_console.print.called


def test_stats_command_missing_files(tmp_path):
    """Stats command handles missing manifest gracefully."""
    with patch('webarc.cli.commands.console') as mock_console:
        with pytest.raises(typer.Exit):
            stats(output_dir=str(tmp_path))
        mock_console.print.assert_called()


def test_stats_command():
    """Test stats command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        # Create manifest file
        manifest_file = output_dir / 'manifest.jsonl'
        with open(manifest_file, 'wb') as f:
            for i in range(3):
                entry = {
                    'url': f'https://example.com/page{i}',
                    'file_path': f'page{i}.md',
                    'word_count': 100 + i * 10,
                    'adapter': 'GenericAdapter',
                    'quality_status': 'ok',
                }
                f.write(orjson.dumps(entry) + b'\n')
        
        # Create graph file
        graph_file = output_dir / 'graph.jsonl'
        with open(graph_file, 'wb') as f:
            entry = {
                'source_url': 'https://example.com/page0',
                'target_url': 'https://example.com/page1',
                'link_type': 'internal',
            }
            f.write(orjson.dumps(entry) + b'\n')
        
        with patch('webarc.cli.commands.console') as mock_console:
            stats(output_dir=str(output_dir))
            
            assert mock_console.print.called


def test_crawl_command():
    """Test crawl command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        
        with patch('webarc.cli.commands.console') as mock_console:
            with patch('webarc.crawler.runner.WebArcCrawler') as mock_crawler_class:
                mock_crawler = MagicMock()
                mock_crawler.run.return_value = {
                    'pages_crawled': 5,
                    'pages_extracted': 4,
                    'pages_skipped': 1,
                    'errors': 0,
                }
                mock_crawler_class.return_value = mock_crawler
                
                try:
                    crawl(
                        seed='https://example.com',
                        allow_domain=None,
                        allow_prefix=None,
                        depth=2,
                        out=str(output_dir),
                        force_js=False,
                        ignore_robots=False,
                        config_file=None,
                        min_content_density=0.1,
                        min_word_count=10,
                        user_agent="TestAgent/1.0",
                        version_lock="/1.2.3/",
                    )
                except Exception:
                    pass  # May raise exceptions during test
                
                assert mock_console.print.called
                assert mock_crawler_class.called
                assert mock_crawler_class.called
                
                passed_config = mock_crawler_class.call_args.kwargs['config']
                assert passed_config.extraction.min_content_density == 0.1
                assert passed_config.extraction.min_word_count == 10
                assert passed_config.crawler.user_agent == "TestAgent/1.0"
                assert mock_crawler_class.call_args.kwargs['version_lock'] == "/1.2.3/"


def test_crawl_command_exception(tmp_path):
    """Exceptions bubbling from the crawler are surfaced."""
    with patch('webarc.cli.commands.console'):
        with patch('webarc.crawler.runner.WebArcCrawler') as mock_crawler_class:
            mock_crawler = MagicMock()
            mock_crawler.run.side_effect = RuntimeError("boom")
            mock_crawler_class.return_value = mock_crawler
            with pytest.raises(RuntimeError):
                crawl(
                    seed='https://example.com',
                    allow_domain=None,
                    allow_prefix=None,
                    depth=1,
                    out=str(tmp_path),
                    force_js=False,
                    ignore_robots=False,
                    config_file=None,
                )


def test_fetch_command(tmp_path):
    """Test fetch command."""
    urls_file = Path(tmp_path) / 'urls.txt'
    urls_file.write_text(
        "https://example.com/file1\n"
        "# comment line\n"
        "https://example.com/file2\n"
        "https://example.com/file1\n"
    )

    with patch('webarc.cli.commands.console') as mock_console:
        with patch('webarc.cli.commands.WebArcFetcher') as mock_fetcher_class:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch.return_value = {
                'pages_fetched': 3,
                'pages_extracted': 2,
                'pages_skipped': 1,
                'errors': 0,
            }
            mock_fetcher_class.return_value = mock_fetcher

            from webarc.cli import commands as cli_commands

            cli_commands.fetch(
                url=['https://example.com/root'],
                urls_file=urls_file,
                out=str(tmp_path),
                config_file=None,
                min_content_density=0.05,
                min_word_count=25,
                user_agent="TestAgent/2.0",
            )

            mock_fetcher_class.assert_called_once()
            args, kwargs = mock_fetcher_class.call_args
            config = kwargs['config']
            assert config.extraction.min_content_density == 0.05
            assert config.extraction.min_word_count == 25
            assert config.crawler.user_agent == "TestAgent/2.0"
            mock_fetcher.fetch.assert_called_once_with([
                'https://example.com/root',
                'https://example.com/file1',
                'https://example.com/file2',
            ])
            assert mock_console.print.called


def test_fetch_command_no_urls(tmp_path):
    """Fetch exits with typer.Exit when no URLs are supplied."""
    with patch('webarc.cli.commands.console'):
        with pytest.raises(typer.Exit):
            from webarc.cli import commands as cli_commands

            cli_commands.fetch(
                url=[],
                urls_file=None,
                out=str(tmp_path),
                config_file=None,
            )


def test_resume_command():
    """Test resume command."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        state_file = output_dir / 'resume.jsonl'
        
        # Create state file
        state_data = {
            'seed_url': 'https://example.com',
            'pages_crawled': 10,
            'visited': ['https://example.com/page1', 'https://example.com/page2'],
        }
        with open(state_file, 'wb') as f:
            f.write(orjson.dumps(state_data))
        
        with patch('webarc.cli.commands.console') as mock_console:
            with patch('webarc.crawler.runner.WebArcCrawler') as mock_crawler_class:
                mock_crawler = MagicMock()
                mock_crawler.run.return_value = {
                    'pages_crawled': 15,
                    'pages_extracted': 12,
                    'pages_skipped': 3,
                    'errors': 0,
                }
                mock_crawler_class.return_value = mock_crawler
                
                try:
                    resume(
                        state_file=str(state_file),
                        out=str(output_dir),
                        config_file=None,
                    )
                except Exception:
                    pass  # May raise exceptions during test
                
                assert mock_console.print.called


def test_resume_command_missing_state(tmp_path):
    """Resume exits when state file is missing."""
    with patch('webarc.cli.commands.console'):
        with pytest.raises(typer.Exit):
            resume(
                state_file=str(tmp_path / "missing.jsonl"),
                out=str(tmp_path),
                config_file=None,
            )


def test_resume_command_invalid_state():
    """Test resume command with invalid state file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        output_dir = Path(tmpdir)
        state_file = output_dir / 'resume.jsonl'
        
        # Create invalid state file (missing seed_url)
        state_data = {
            'pages_crawled': 10,
        }
        with open(state_file, 'wb') as f:
            f.write(orjson.dumps(state_data))
        
        with patch('webarc.cli.commands.console') as mock_console:
            try:
                resume(
                    state_file=str(state_file),
                    out=str(output_dir),
                    config_file=None,
                )
            except (SystemExit, typer.Exit, ClickExit):
                pass  # Expected exit code 1
            
            assert mock_console.print.called


def test_load_urls_filtering(tmp_path):
    """_load_urls helper filters comments/empties and deduplicates."""
    urls_file = tmp_path / "urls.txt"
    urls_file.write_text(
        """
        https://example.com/a
        # comment
        https://example.com/b
        https://example.com/a
        """.strip()
    )
    urls = _load_urls(["https://example.com/root"], urls_file)
    assert urls == [
        "https://example.com/root",
        "https://example.com/a",
        "https://example.com/b",
    ]
