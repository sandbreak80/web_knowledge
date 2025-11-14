"""Integration tests for WebArcFetcher across multiple adapters."""

from pathlib import Path
from types import SimpleNamespace

from webarc.config.loader import load_config
from webarc.crawler.runner import WebArcFetcher


def test_fetcher_processes_mkdocs_sphinx_news(tmp_path, monkeypatch):
    config = load_config()
    config.extraction.min_word_count = 1
    config.extraction.min_content_density = 0
    config.extraction.require_heading = False
    config.output.obsidian_link_style = "wikilink"

    fetcher = WebArcFetcher(config=config, output_dir=Path(tmp_path))

    config.adapters.reddit.use_json_api = False

    html_map = {
        "https://example.com/docs/mkdocs": """
        <html><body>
          <div class="md-content">
            <h1>MkDocs Title</h1>
            <p>{paragraph}</p>
            <a href="/docs/relative">Relative</a>
          </div>
        </body></html>
        """.format(paragraph=" ".join(["content"] * 60)),
        "https://example.com/docs/sphinx": """
        <html><body>
          <div class="body">
            <h1>Sphinx Title</h1>
            <p>{paragraph}</p>
          </div>
        </body></html>
        """.format(paragraph=" ".join(["content"] * 60)),
        "https://example.com/news/story": """
        <html>
          <head><meta property="og:type" content="article" /></head>
          <body>
            <article>
              <h1>News Headline</h1>
              <p>{paragraph}</p>
            </article>
          </body>
        </html>
        """.format(paragraph=" ".join(["story"] * 60)),
        "https://example.com/confluence/page": """
        <html>
          <body>
            <div id="main-content">
              <h1>Confluence Page</h1>
              <div class="scroll-to-top">skip me</div>
              <p>{paragraph}</p>
            </div>
          </body>
        </html>
        """.format(paragraph=" ".join(["doc"] * 60)),
        "https://example.com/reddit/thread": """
        <html>
          <body>
            <div id="shortlink-text">
              <h1>Reddit Thread</h1>
            </div>
            <div data-test-id="post-content">
              <p>{paragraph}</p>
            </div>
          </body>
        </html>
        """.format(paragraph=" ".join(["comment"] * 60)),
    }

    class DummyResponse:
        def __init__(self, text):
            self.status_code = 200
            self.text = text

    def fake_get(url, timeout, headers):
        return DummyResponse(html_map[url])

    monkeypatch.setattr(
        "webarc.crawler.runner.requests",
        SimpleNamespace(get=fake_get),
    )

    stats = fetcher.fetch(list(html_map.keys()))

    assert stats["pages_fetched"] == len(html_map)
    assert stats["pages_extracted"] == len(html_map)
    output_files = list(Path(tmp_path).glob("**/*.md"))
    assert len(output_files) == len(html_map)

