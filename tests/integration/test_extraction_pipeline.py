"""Integration tests for the extraction pipeline."""

from pathlib import Path

import pytest

from webarc.config.loader import load_config
from webarc.crawler.runner import ExtractionPipeline
from webarc.adapters.router import AdapterRouter
from webarc.html2md.converter import ObsidianMarkdownConverter
from webarc.output.manifest import ManifestWriter
from webarc.output.writer import OutputWriter
from webarc.crawler.pipelines import DuplicateFilterPipeline


@pytest.fixture
def pipeline(tmp_path):
    config = load_config()
    config.extraction.min_word_count = 1
    config.extraction.min_content_density = 0
    config.extraction.require_heading = False
    output_dir = Path(tmp_path)
    return ExtractionPipeline(
        config=config,
        output_dir=output_dir,
        output_writer=OutputWriter(output_dir, config),
        manifest_writer=ManifestWriter(output_dir),
        adapter_router=AdapterRouter(config),
        markdown_converter=ObsidianMarkdownConverter(config),
    )


def test_pipeline_process_success(pipeline, tmp_path):
    html = """
    <html>
      <body>
        <main>
          <h1>Title</h1>
          <p>{text}</p>
        </main>
      </body>
    </html>
    """.format(text=" ".join(["content"] * 80))
    result = pipeline.process("https://example.com/page", html, 200)
    assert result["success"] is True
    assert result["file_path"].exists()


def test_pipeline_process_rejected(pipeline):
    html = "<html><body><p>Too short</p></body></html>"
    result = pipeline.process("https://example.com/short", html, 200)
    assert result["success"] is False


def test_duplicate_filter_pipeline():
    pipeline = DuplicateFilterPipeline()
    item = {"url": "https://example.com/page"}
    assert pipeline.process_item(item.copy(), None) == item
    assert pipeline.process_item(item.copy(), None) is None

