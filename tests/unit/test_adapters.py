"""Unit tests for adapter system."""

import pytest
from bs4 import BeautifulSoup
from unittest.mock import patch
from webarc.adapters.confluence import ConfluenceAdapter
from webarc.adapters.mkdocs import MkDocsAdapter
from webarc.adapters.sphinx import SphinxAdapter
from webarc.adapters.generic import GenericAdapter
from webarc.adapters.news import NewsAdapter
from webarc.adapters.reddit import RedditAdapter
from webarc.adapters.squarespace import SquarespaceAdapter
from webarc.adapters.router import AdapterRouter
from webarc.config.loader import load_config


@pytest.fixture
def config():
    """Load test configuration."""
    return load_config()


def test_confluence_adapter_matches(config):
    """Test Confluence adapter matching."""
    adapter = ConfluenceAdapter(config)
    
    html = """
    <html>
    <body>
        <div class="confluence-content">
            <h1>Title</h1>
            <p>Content</p>
        </div>
    </body>
    </html>
    """
    
    assert adapter.matches("https://docs.appdynamics.com/page", html) is True


def test_generic_adapter_always_matches(config):
    """Test that generic adapter always matches."""
    adapter = GenericAdapter(config)
    assert adapter.matches("https://example.com/page", "<html></html>") is True


def test_adapter_router(config):
    """Test adapter router selection."""
    router = AdapterRouter(config)
    
    html = """
    <html>
    <body>
        <div class="confluence-content">Content</div>
    </body>
    </html>
    """
    
    adapter = router.get_adapter("https://docs.appdynamics.com/page", html)
    assert isinstance(adapter, ConfluenceAdapter)
    
    # Generic should match anything
    adapter2 = router.get_adapter("https://example.com/page", "<html></html>")
    assert isinstance(adapter2, GenericAdapter)

    squarespace_html = """
    <html>
    <body>
        <div class="sqs-layout">
            <h1>Squarespace Title</h1>
            <p>Squarespace content</p>
        </div>
    </body>
    </html>
    """
    adapter3 = router.get_adapter("https://example.squarespace.com/page", squarespace_html)
    assert isinstance(adapter3, SquarespaceAdapter)

    news_html = """
    <html>
    <head>
        <meta property="og:type" content="article">
        <title>News story</title>
    </head>
    <body>
        <article>
            <h1>Breaking News</h1>
            <p>Summary of the story.</p>
        </article>
    </body>
    </html>
    """
    adapter4 = router.get_adapter("https://news.example.com/story", news_html)
    assert isinstance(adapter4, NewsAdapter)


def test_confluence_extract_content(config):
    """Test Confluence content extraction."""
    adapter = ConfluenceAdapter(config)
    
    html = """
    <html lang="en">
    <body>
        <div class="confluence-content">
            <h1>Main Title</h1>
            <p>Content paragraph</p>
        </div>
        <div class="footer">Footer</div>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'lxml')
    result = adapter.extract_content(soup, "https://docs.appdynamics.com/appd/24.x/en/page")
    
    assert result['title'] == "Main Title"
    assert "Main Title" in result['body_html']
    assert result['framework'] == "confluence-viewport"
    assert result['lang'] == "en"


def test_confluence_matches_config_domain(config):
    """Config domain list forces Confluence match without markers."""
    config.adapters.confluence.domains.append("custom.example.com")
    adapter = ConfluenceAdapter(config)
    assert adapter.matches("https://custom.example.com/page", "<html></html>")


def test_confluence_extract_removes_widgets(config):
    """Ensure extra Confluence widgets are stripped."""
    adapter = ConfluenceAdapter(config)
    html = """
    <html>
      <body>
        <div class="confluence-content">
          <h1>Title</h1>
          <div class="appdtocbox">TOC</div>
          <div class="scroll-pdf-modal">Modal</div>
          <style>.foo { color:red; }</style>
          <p>Body</p>
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, "https://docs.appdynamics.com/appd/25.10/en/title")
    assert "TOC" not in result["body_html"]
    assert "Modal" not in result["body_html"]
    assert "<style" not in result["body_html"]


def test_confluence_transform_links(config):
    """Verify version-aware link transformation."""
    adapter = ConfluenceAdapter(config)
    source = "https://docs.appdynamics.com/appd/25.10.0/en/source"
    links = adapter.transform_links(
        source,
        [
            "https://docs.appdynamics.com/appd/25.10.0/en/child",
            "https://docs.appdynamics.com/appd/24.9.0/en/other",
            "https://example.com/external",
        ],
    )
    assert links[0] == "[[child]]"
    assert links[1] == "[External](https://docs.appdynamics.com/appd/24.9.0/en/other)"
    assert links[2] == "https://example.com/external"


def test_generic_adapter_fallback_to_main(config):
    """Ensure generic adapter falls back to <main> when readability output is too small."""
    adapter = GenericAdapter(config)
    
    html = """
    <html lang="en">
    <body>
        <main>
            <h1>Main Heading</h1>
            <p>{paragraph}</p>
        </main>
    </body>
    </html>
    """.format(paragraph=" ".join(["content"] * 120))
    
    soup = BeautifulSoup(html, 'lxml')
    
    with patch('webarc.adapters.generic.extract_main_content', return_value="<p>Too short</p>"):
        result = adapter.extract_content(soup, "https://example.com/")
    
    assert "Main Heading" in result['body_html']
    assert "content content" in result['body_html']
    assert result['framework'] == "generic"


def test_squarespace_adapter_matches(config):
    """Squarespace adapter detects Squarespace markup."""
    adapter = SquarespaceAdapter(config)

    html = """
    <html>
    <head>
        <meta name="generator" content="Squarespace 7.1" />
    </head>
    <body>
        <div class="sqs-layout">
            <h1>Squarespace Title</h1>
            <p>Squarespace content block</p>
        </div>
    </body>
    </html>
    """
    assert adapter.matches("https://example.squarespace.com/", html) is True


def test_squarespace_extract_content(config):
    """Ensure Squarespace adapter extracts main content and removes boilerplate."""
    adapter = SquarespaceAdapter(config)

    html = """
    <html lang="en">
    <body>
        <header class="Header">Nav</header>
        <div class="sqs-layout">
            <h1>Squarespace Title</h1>
            <p>{body}</p>
        </div>
        <footer class="Footer">Footer content</footer>
    </body>
    </html>
    """.format(body=" ".join(["content"] * 50))

    soup = BeautifulSoup(html, 'lxml')
    result = adapter.extract_content(soup, "https://example.squarespace.com/page")

    assert result['title'] == "Squarespace Title"
    assert "Footer" not in result['body_html']
    assert "Nav" not in result['body_html']
    assert "content content" in result['body_html']
    assert result['framework'] == "squarespace"
    assert result['lang'] == "en"


def test_news_adapter_matches(config):
    """NewsAdapter detects article markup."""
    adapter = NewsAdapter(config)

    html = """
    <html>
    <head>
        <meta property="og:type" content="article" />
    </head>
    <body>
        <article>
            <h1>Headline</h1>
            <p>Story</p>
        </article>
    </body>
    </html>
    """
    assert adapter.matches("https://news.example.com/story", html)


def test_news_adapter_extract_content(config):
    """NewsAdapter extracts article content."""
    adapter = NewsAdapter(config)

    html = """
    <html lang="en">
    <body>
        <header>Nav</header>
        <article>
            <h1>Headline</h1>
            <p>{body}</p>
        </article>
        <footer>footer</footer>
    </body>
    </html>
    """.format(body=" ".join(["news"] * 80))

    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, "https://news.example.com/story")

    assert result["title"] == "Headline"
    assert "Nav" not in result["body_html"]
    assert "footer" not in result["body_html"]
    assert "news news" in result["body_html"]
    assert result["framework"] == "news"


def test_reddit_adapter_matches(config):
    """Reddit adapter should match reddit domains."""
    adapter = RedditAdapter(config)
    assert adapter.matches("https://www.reddit.com/r/homelab/", "<html></html>")
    assert adapter.matches("https://redd.it/abc123", "<html></html>")


def test_reddit_adapter_extract_listing(monkeypatch, config):
    """Ensure Reddit adapter renders listing JSON into HTML."""
    adapter = RedditAdapter(config)

    sample_payload = {
        "data": {
            "title": "r/homelab",
            "display_name": "homelab",
            "children": [
                {
                    "data": {
                        "title": "Interesting Setup",
                        "author": "user123",
                        "score": 420,
                        "permalink": "/r/homelab/comments/xyz/interesting_setup/",
                        "selftext_html": "<p>body</p>",
                    }
                }
            ],
        }
    }

    class DummyResponse:
        def __init__(self, json_payload):
            self._payload = json_payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, headers, timeout):
        assert url.endswith(".json")
        return DummyResponse(sample_payload)

    monkeypatch.setattr("webarc.adapters.reddit.requests.get", fake_get)

    soup = BeautifulSoup("<html></html>", "lxml")
    result = adapter.extract_content(soup, "https://www.reddit.com/r/homelab/")

    assert "Interesting Setup" in result["body_html"]
    assert "user123" in result["body_html"]
    assert result["framework"] == "reddit-json"


def test_reddit_adapter_extract_comments(monkeypatch, config):
    """Ensure Reddit adapter renders comment threads."""
    adapter = RedditAdapter(config)

    sample_payload = [
        {
            "data": {
                "children": [
                    {
                        "data": {
                            "title": "AMA",
                            "author": "poster",
                            "score": 1337,
                            "permalink": "/r/homelab/comments/abc/ama/",
                            "selftext_html": "<p>Hello world</p>",
                        }
                    }
                ]
            }
        },
        {
            "data": {
                "children": [
                    {
                        "kind": "t1",
                        "data": {
                            "author": "commenter",
                            "score": 10,
                            "body_html": "<p>Nice lab!</p>",
                            "replies": "",
                        },
                    },
                    {
                        "kind": "t1",
                        "data": {
                            "author": "nested",
                            "score": 5,
                            "body_html": "<p>Second level!</p>",
                            "replies": {
                                "data": {
                                    "children": [
                                        {
                                            "kind": "t1",
                                            "data": {
                                                "author": "depth2",
                                                "score": 1,
                                                "body_html": "<p>Depth limited</p>",
                                                "replies": "",
                                            },
                                        }
                                    ]
                                }
                            },
                        },
                    },
                ]
            }
        },
    ]

    class DummyResponse:
        def __init__(self, json_payload):
            self._payload = json_payload

        def raise_for_status(self):
            return None

        def json(self):
            return self._payload

    def fake_get(url, headers, timeout):
        return DummyResponse(sample_payload)

    monkeypatch.setattr("webarc.adapters.reddit.requests.get", fake_get)

    soup = BeautifulSoup("<html></html>", "lxml")
    result = adapter.extract_content(soup, "https://www.reddit.com/r/homelab/comments/abc/ama/")

    assert "AMA" in result["body_html"]
    assert "commenter" in result["body_html"]
    assert "Nice lab" in result["body_html"]
    assert "Second level" in result["body_html"]
    # Depth limit prevents rendering beyond 2 levels
    assert "Depth limited" in result["body_html"]


def test_squarespace_adapter_disabled(config):
    """Disabled Squarespace adapter should not match."""
    config.adapters.squarespace.enabled = False
    adapter = SquarespaceAdapter(config)
    html = '<html><body><div class="sqs-layout">Content</div></body></html>'
    assert adapter.matches("https://example.squarespace.com/", html) is False


def test_news_adapter_disabled(config):
    """Disabled News adapter should not match even with signals."""
    config.adapters.news.enabled = False
    adapter = NewsAdapter(config)
    html = '<html><body><article><h1>Headline</h1></article></body></html>'
    assert adapter.matches("https://news.example.com/story", html) is False


def test_news_adapter_fallback_to_body(config):
    """News adapter falls back to <body> when no known selectors match."""
    adapter = NewsAdapter(config)
    html = """
    <html lang="en">
        <body>
            <header>Header</header>
            <div class="content">
                <h1>Fallback Title</h1>
                <p>{body}</p>
            </div>
            <div class="advertisement">Ad</div>
            <footer>Footer</footer>
        </body>
    </html>
    """.format(body=" ".join(["news"] * 60))
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, "https://news.example.com/fallback")
    assert result["title"] == "Fallback Title"
    assert "advertisement" not in result["body_html"].lower()
    assert "news news" in result["body_html"]


def test_reddit_adapter_disabled(config):
    """Disabled Reddit adapter ignores reddit domains."""
    config.adapters.reddit.enabled = False
    adapter = RedditAdapter(config)
    assert adapter.matches("https://www.reddit.com/r/test/", "") is False


def test_reddit_adapter_html_fallback(config):
    """When JSON API is disabled, fallback to raw HTML extraction."""
    config.adapters.reddit.use_json_api = False
    adapter = RedditAdapter(config)
    soup = BeautifulSoup("<html><body><h1>Post</h1></body></html>", "lxml")
    result = adapter.extract_content(soup, "https://www.reddit.com/r/test/comments/123/")
    assert result["framework"] == "reddit-html"
    assert "Post" in result["body_html"]


def test_reddit_adapter_error_path(monkeypatch, config):
    """Errors while fetching JSON should be reported in metadata."""
    adapter = RedditAdapter(config)

    def boom(self, url):
        raise RuntimeError("network down")

    monkeypatch.setattr(RedditAdapter, "_fetch_json", boom)
    soup = BeautifulSoup("<html></html>", "lxml")
    result = adapter.extract_content(soup, "https://www.reddit.com/r/test/")
    assert result["metadata"]["error"] == "network down"


def test_squarespace_adapter_custom_selectors(config):
    """Custom selectors provided via config are honored."""
    config.adapters.squarespace.content_selectors = ['.custom-main']
    config.adapters.squarespace.remove_selectors = ['.remove-me']
    adapter = SquarespaceAdapter(config)

    html = """
    <html lang="en">
        <body>
            <div class="custom-main">
                <h1>Configured Title</h1>
                <p>Configured content</p>
            </div>
            <div class="remove-me">Should vanish</div>
        </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, "https://example.squarespace.com/custom")
    assert "Configured Title" in result["body_html"]
    assert "Should vanish" not in result["body_html"]


def test_mkdocs_adapter_matches(config):
    """Test MkDocs adapter matching."""
    adapter = MkDocsAdapter(config)
    
    html = """
    <html>
    <head>
        <meta name="generator" content="mkdocs">
    </head>
    <body>
        <div class="md-content">
            <h1>Title</h1>
            <p>Content</p>
        </div>
    </body>
    </html>
    """
    
    assert adapter.matches("https://example.com/docs/page", html) is True


def test_mkdocs_adapter_disabled(config):
    """Adapter should not match when disabled via config."""
    config.adapters.mkdocs.enabled = False
    adapter = MkDocsAdapter(config)
    assert adapter.matches("https://example.com/docs/page", "<html></html>") is False


def test_mkdocs_extract_content(config):
    """Test MkDocs content extraction."""
    adapter = MkDocsAdapter(config)
    
    html = """
    <html lang="en">
    <body>
        <div class="md-content">
            <h1>MkDocs Title</h1>
            <p>MkDocs content</p>
        </div>
        <div class="md-sidebar">Sidebar</div>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'lxml')
    result = adapter.extract_content(soup, "https://example.com/docs/page")
    
    assert result['title'] == "MkDocs Title"
    assert "MkDocs content" in result['body_html']
    assert result['framework'] == "mkdocs"
    assert result['lang'] == "en"


def test_mkdocs_fallback_readability(monkeypatch, config):
    """Fallback extraction uses readability when selector missing."""
    adapter = MkDocsAdapter(config)
    html = "<html><body><p>No selectors present</p></body></html>"
    soup = BeautifulSoup(html, "lxml")

    monkeypatch.setattr(
        "webarc.adapters.mkdocs.extract_main_content",
        lambda html_str, url: "<p>Readability</p>",
    )

    result = adapter.extract_content(soup, "https://example.com/docs/page")
    assert "Readability" in result["body_html"]


def test_mkdocs_custom_selectors(config):
    """Custom selectors remove unwanted nodes."""
    config.adapters.mkdocs.content_selector = ".article"
    config.adapters.mkdocs.remove_selectors = [".remove"]
    adapter = MkDocsAdapter(config)
    html = """
    <html>
      <body>
        <div class="article">
          <h1>Custom</h1>
          <p>Keep me</p>
          <div class="remove">Drop me</div>
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, "https://example.com/docs/custom")
    assert "Drop me" not in result["body_html"]
    assert "Keep me" in result["body_html"]


def test_sphinx_adapter_matches(config):
    """Test Sphinx adapter matching."""
    adapter = SphinxAdapter(config)
    
    html = """
    <html>
    <head>
        <meta name="generator" content="Sphinx">
    </head>
    <body>
        <div class="body">
            <h1>Title</h1>
            <p>Content</p>
        </div>
    </body>
    </html>
    """
    
    assert adapter.matches("https://example.com/docs/page", html) is True


def test_sphinx_adapter_disabled(config):
    """Adapter should not match when disabled."""
    config.adapters.sphinx.enabled = False
    adapter = SphinxAdapter(config)
    assert adapter.matches("https://example.com/docs/page", "<html></html>") is False


def test_sphinx_extract_content(config):
    """Test Sphinx content extraction."""
    adapter = SphinxAdapter(config)
    
    html = """
    <html lang="en">
    <body>
        <div class="body">
            <h1>Sphinx Title</h1>
            <p>Sphinx content</p>
        </div>
        <div class="sphinxsidebar">Sidebar</div>
    </body>
    </html>
    """
    
    soup = BeautifulSoup(html, 'lxml')
    result = adapter.extract_content(soup, "https://example.com/docs/page")
    
    assert result['title'] == "Sphinx Title"
    assert "Sphinx content" in result['body_html']
    assert result['framework'] == "sphinx"
    assert result['lang'] == "en"


def test_sphinx_fallback_readability(monkeypatch, config):
    """Sphinx adapter falls back to readability when selectors missing."""
    adapter = SphinxAdapter(config)
    monkeypatch.setattr(
        "webarc.adapters.sphinx.extract_main_content",
        lambda html_str, url: "<p>Fallback</p>",
    )
    soup = BeautifulSoup("<html><body><p>None</p></body></html>", "lxml")
    result = adapter.extract_content(soup, "https://example.com/docs/page")
    assert "Fallback" in result["body_html"]


def test_sphinx_custom_selectors(config):
    """Custom selectors control removal behaviour."""
    config.adapters.sphinx.content_selector = ".document"
    config.adapters.sphinx.remove_selectors = [".remove"]
    adapter = SphinxAdapter(config)
    html = """
    <html>
      <body>
        <div class="document">
          <h1>Doc</h1>
          <div class="remove">Trash</div>
          <p>Keep</p>
        </div>
      </body>
    </html>
    """
    soup = BeautifulSoup(html, "lxml")
    result = adapter.extract_content(soup, "https://example.com/docs/doc")
    assert "Trash" not in result["body_html"]
    assert "Keep" in result["body_html"]


def test_adapter_router_with_mkdocs(config):
    """Test adapter router with MkDocs."""
    router = AdapterRouter(config)
    
    html = """
    <html>
    <body>
        <div class="md-content">MkDocs Content</div>
    </body>
    </html>
    """
    
    adapter = router.get_adapter("https://example.com/docs/page", html)
    assert isinstance(adapter, MkDocsAdapter)


def test_adapter_router_with_sphinx(config):
    """Test adapter router with Sphinx."""
    router = AdapterRouter(config)
    
    html = """
    <html>
    <body>
        <div class="body">Sphinx Content</div>
    </body>
    </html>
    """
    
    adapter = router.get_adapter("https://example.com/docs/page", html)
    assert isinstance(adapter, SphinxAdapter)
