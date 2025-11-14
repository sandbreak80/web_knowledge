"""Integration coverage for adapter matching and extraction."""

from bs4 import BeautifulSoup

from webarc.config.loader import load_config
from webarc.adapters.confluence import ConfluenceAdapter
from webarc.adapters.generic import GenericAdapter
from webarc.adapters.mkdocs import MkDocsAdapter
from webarc.adapters.sphinx import SphinxAdapter
from webarc.adapters.news import NewsAdapter
from webarc.adapters.reddit import RedditAdapter


def test_confluence_adapter_flow():
    config = load_config()
    config.adapters.confluence.domains.append("example.com")
    adapter = ConfluenceAdapter(config)
    url = "https://example.com/appd/25.0/en/page"
    html = """
    <html lang="en">
      <body>
        <div id="main-content">
          <h1>Confluence Title</h1>
          <div class="scroll-to-top">hide</div>
          <div class="page-metadata">meta</div>
          <p>Body text</p>
        </div>
      </body>
    </html>
    """
    assert adapter.matches(url, html)
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, url)
    assert result["title"] == "Confluence Title"
    assert "scroll-to-top" not in result["body_html"]
    links = adapter.transform_links(
        url,
        [
            "https://example.com/appd/25.0/en/other",
            "https://example.com/appd/24.0/en/legacy",
            "https://other.com/page",
        ],
    )
    assert "[[other]]" in links[0]
    assert "[External]" in links[1]


def test_mkdocs_adapter_extracts_content():
    config = load_config()
    adapter = MkDocsAdapter(config)
    html = """
    <html><body>
      <div class="md-main__inner">
        <h1>MkDocs Heading</h1>
        <p>Some docs text.</p>
      </div>
    </body></html>
    """
    url = "https://docs.example.com/guide"
    assert adapter.matches(url, html)
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, url)
    assert "MkDocs Heading" in result["body_html"]


def test_sphinx_adapter_extracts_content():
    config = load_config()
    adapter = SphinxAdapter(config)
    html = """
    <html><body>
      <div class="body">
        <h1>Sphinx Title</h1>
        <p>Sphinx body content.</p>
      </div>
    </body></html>
    """
    url = "https://docs.example.com/sphinx"
    assert adapter.matches(url, html)
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, url)
    assert "Sphinx body content." in result["body_html"]


def test_news_adapter_detects_article():
    config = load_config()
    adapter = NewsAdapter(config)
    html = """
    <html>
      <head><meta property="og:type" content="article" /></head>
      <body>
        <header>Nav</header>
        <article>
          <h1>News Title</h1>
          <p>Breaking news body.</p>
        </article>
      </body>
    </html>
    """
    url = "https://news.example.com/story"
    assert adapter.matches(url, html)
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, url)
    assert "Breaking news body." in result["body_html"]


def test_reddit_adapter_html_fallback(monkeypatch):
    config = load_config()
    config.adapters.reddit.use_json_api = False
    adapter = RedditAdapter(config)
    html = """
    <html><body>
      <title>Reddit Title</title>
      <div id="shortlink-text">
        <h1>Thread Title</h1>
      </div>
      <div data-test-id="post-content">
        <p>Reddit body.</p>
      </div>
    </body></html>
    """
    url = "https://www.reddit.com/r/test/comments/abc123/thread/"
    assert adapter.matches(url, html)
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, url)
    assert "Reddit body." in result["body_html"]


def test_reddit_adapter_json(monkeypatch):
    config = load_config()
    config.adapters.reddit.use_json_api = True
    adapter = RedditAdapter(config)
    url = "https://www.reddit.com/r/test/comments/abc123/thread/"

    payload = [
        {
            "data": {
                "children": [
                    {"data": {"title": "Post Title", "permalink": "/r/test/comments/abc123/thread/", "selftext_html": "<p>Body</p>", "author": "alice", "score": 10}}
                ]
            }
        },
        {
            "data": {
                "children": [
                    {"kind": "t1", "data": {"author": "bob", "score": 5, "body_html": "<p>Comment</p>"},},
                ]
            }
        },
    ]

    class DummyResponse:
        def __init__(self, json_data):
            self._json = json_data
            self.status_code = 200

        def raise_for_status(self):
            return None

        def json(self):
            return self._json

    def fake_get(url, headers, timeout):
        return DummyResponse(payload)

    monkeypatch.setattr("webarc.adapters.reddit.requests.get", fake_get)

    soup = BeautifulSoup("<html></html>", "lxml")
    result = adapter.extract_content(soup, url)
    assert "Post Title" in result["body_html"]
    assert "Comment" in result["body_html"]
    links = adapter.transform_links(url, ["/r/test"])
    assert links == ["https://www.reddit.com/r/test"]


def test_generic_adapter_fallback(monkeypatch):
    config = load_config()
    config.extraction.min_word_count = 50
    adapter = GenericAdapter(config)
    html = """
    <html><body>
      <main>
        <h1>Generic Title</h1>
        <div class="sqs-layout">
          <p>{text}</p>
        </div>
      </main>
    </body></html>
    """.format(text=" ".join(["Square", "content"] * 40))
    url = "https://site.example.com/page"
    soup = BeautifulSoup(html, "lxml")
    monkeypatch.setattr("webarc.adapters.generic.extract_main_content", lambda html, url: "<p>short</p>")
    result = adapter.extract_content(soup, url)
    assert "Square content" in result["body_html"]

