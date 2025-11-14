"""Integration-style tests for ExtractionPipeline with specific adapters."""

from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
import pytest

from webarc.config.loader import load_config
from webarc.crawler.runner import ExtractionPipeline, WebArcCrawler
from webarc.adapters.router import AdapterRouter
from webarc.html2md.converter import ObsidianMarkdownConverter
from webarc.output.manifest import ManifestWriter
from webarc.output.writer import OutputWriter


@pytest.fixture
def tuned_config():
    """Return a config tuned for synthetic content."""
    cfg = load_config()
    cfg.extraction.min_content_density = 0
    cfg.extraction.min_content_length = 0
    cfg.extraction.min_word_count = 1
    cfg.extraction.require_heading = False
    return cfg


def build_pipeline(config, tmp_path: Path) -> ExtractionPipeline:
    output_writer = OutputWriter(tmp_path, config)
    manifest_writer = ManifestWriter(tmp_path)
    adapter_router = AdapterRouter(config)
    markdown_converter = ObsidianMarkdownConverter(config)
    return ExtractionPipeline(
        config=config,
        output_dir=tmp_path,
        output_writer=output_writer,
        manifest_writer=manifest_writer,
        adapter_router=adapter_router,
        markdown_converter=markdown_converter,
    )


def test_pipeline_with_squarespace_adapter(tmp_path, tuned_config):
    """Squarespace HTML passes through the pipeline producing Markdown."""
    pipeline = build_pipeline(tuned_config, Path(tmp_path))
    html = """
    <html>
        <body>
            <div class="sqs-layout">
                <h1>Squarespace Title</h1>
                <p>{body}</p>
            </div>
            <footer class="Footer">Footer content</footer>
        </body>
    </html>
    """.format(body=" ".join(["content"] * 80))

    result = pipeline.process(
        "https://cherylscaramels.com/",
        html,
        200,
    )

    assert result["success"] is True
    assert result["metadata"]["adapter"] == "SquarespaceAdapter"
    output_path = result["file_path"]
    assert output_path.exists()
    content = output_path.read_text()
    assert "Squarespace Title" in content
    assert "Footer content" not in content


def test_pipeline_with_news_adapter(tmp_path, tuned_config):
    """NewsAdapter is selected and removes boilerplate elements."""
    pipeline = build_pipeline(tuned_config, Path(tmp_path))
    html = """
    <html lang="en">
        <head><meta property="og:type" content="article"></head>
        <body>
            <article>
                <h1>News Headline</h1>
                <p>{body}</p>
            </article>
            <div class="advertisement">Ad</div>
        </body>
    </html>
    """.format(body=" ".join(["story"] * 60))

    result = pipeline.process(
        "https://www.npr.org/sections/news/",
        html,
        200,
    )

    assert result["success"] is True
    assert result["metadata"]["adapter"] == "NewsAdapter"
    news_markdown = result["file_path"].read_text()
    assert "News Headline" in news_markdown
    assert "advertisement" not in news_markdown.lower()


def test_pipeline_with_reddit_adapter(tmp_path, tuned_config, monkeypatch):
    """Pipeline uses Reddit adapter with JSON rendering."""
    pipeline = build_pipeline(tuned_config, Path(tmp_path))

    sample_payload = {
        "data": {
            "title": "r/test",
            "display_name": "test",
            "children": [
                {
                    "data": {
                        "title": "Interesting post",
                        "author": "author1",
                        "score": 100,
                        "permalink": "/r/test/comments/abc/",
                    }
                }
            ],
        }
    }

    def fake_fetch(self, url):
        return sample_payload

    monkeypatch.setattr(
        "webarc.adapters.reddit.RedditAdapter._fetch_json",
        fake_fetch,
    )

    filler = " ".join(["placeholder"] * 120)
    html = f"<html><body><p>{filler}</p></body></html>"

    monkeypatch.setattr(
        "webarc.crawler.runner.ContentQuality.is_acceptable",
        lambda self, **_: (True, None),
    )

    result = pipeline.process(
        "https://www.reddit.com/r/test/",
        html,
        200,
    )

    assert result["success"] is True
    assert result["metadata"]["adapter"] == "RedditAdapter"

