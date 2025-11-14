"""Integration tests for crawler core."""

from types import SimpleNamespace

import pytest
from scrapy.http import Request, HtmlResponse

from webarc.crawler.spider import WebArcSpider
from webarc.crawler.middlewares import DomainFenceMiddleware
from webarc.config.loader import load_config


@pytest.fixture
def config():
    """Load test configuration."""
    return load_config()


@pytest.fixture
def spider(config):
    """Create test spider."""
    return WebArcSpider(
        seed_url="https://example.com/page",
        config=config,
        allowed_domain="example.com",
        max_depth=2
    )


def test_spider_initialization(spider):
    """Test spider initialization."""
    assert spider.name == "webarc"
    assert spider.seed_url == "https://example.com/page"
    assert spider.max_depth == 2
    assert len(spider.visited_urls) == 0


def test_spider_depth_zero(config):
    """Ensure max_depth=0 is respected."""
    zero_spider = WebArcSpider(
        seed_url="https://example.com/page",
        config=config,
        allowed_domain="example.com",
        max_depth=0,
        version_lock=None,
    )
    assert zero_spider.max_depth == 0

    html = """
    <html>
    <body>
        <a href="https://example.com/other">Other</a>
    </body>
    </html>
    """
    response = HtmlResponse(
        url="https://example.com/page",
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=Request("https://example.com/page"),
    )
    response.meta['depth'] = 0

    results = list(zero_spider.parse(response))
    assert results == []


def test_spider_version_lock(config):
    """Ensure version lock filters links."""
    spider = WebArcSpider(
        seed_url="https://example.com/en/appdynamics/25.10.0/root",
        config=config,
        allowed_domain="example.com",
        max_depth=2,
        version_lock="/25.10.0/",
    )

    html = """
    <html>
      <body>
        <a href="https://example.com/en/appdynamics/25.10.0/child">Same version</a>
        <a href="https://example.com/en/appdynamics/25.9.0/older">Older version</a>
        <a href="https://example.com/en/appdynamics/latest/page">Latest alias</a>
      </body>
    </html>
    """

    request = Request("https://example.com/en/appdynamics/25.10.0/root")
    request.meta['depth'] = 0
    response = HtmlResponse(
        url="https://example.com/en/appdynamics/25.10.0/root",
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=request,
    )

    results = list(spider.parse(response))
    assert len(results) == 1
    assert isinstance(results[0], Request)
    assert results[0].url == "https://example.com/en/appdynamics/25.10.0/child"


def test_start_requests(spider):
    """Test start_requests generation."""
    requests = list(spider.start_requests())
    assert len(requests) == 1
    assert requests[0].url == "https://example.com/page"
    assert requests[0].meta['depth'] == 0


def test_domain_fence_middleware():
    """Test domain fence middleware."""
    middleware = DomainFenceMiddleware(allowed_domain="example.com")
    
    # Allowed domain
    request1 = Request("https://example.com/page")
    result1 = middleware.process_request(request1, None)
    assert result1 is None
    
    # Blocked domain
    request2 = Request("https://other.com/page")
    result2 = middleware.process_request(request2, None)
    assert result2 is not None
    assert result2.status == 403


def test_link_extraction(spider):
    """Test link extraction from HTML."""
    html = """
    <html>
    <body>
        <a href="/page1">Link 1</a>
        <a href="https://example.com/page2">Link 2</a>
        <a href="https://other.com/page3">Link 3</a>
    </body>
    </html>
    """
    
    response = HtmlResponse(
        url="https://example.com/",
        body=html.encode('utf-8')
    )
    
    links = spider._extract_links(response)
    assert len(links) == 3
    assert "/page1" in links
    assert "https://example.com/page2" in links
    assert "https://other.com/page3" in links


def test_safety_guard_checking(spider):
    """Test safety guard checking."""
    # Normal URL should pass
    assert spider._check_safety_guards("https://example.com/page") is True
    
    # Very long URL should fail
    long_url = "https://example.com/" + "a" * 3000
    assert spider._check_safety_guards(long_url) is False


def test_spider_safety_enforce(spider):
    """Safety guard returns False in enforce mode when pattern matches."""
    spider.config.safety.mode = "enforce"
    spider.config.safety.blocked_patterns.append("forbidden")
    assert spider._check_safety_guards("https://example.com/forbidden") is False


def test_spider_errback(spider, caplog):
    """Errback increments error count and logs the failure."""
    from types import SimpleNamespace

    failure = SimpleNamespace(
        request=SimpleNamespace(url="https://example.com/broken"),
        value=RuntimeError("boom"),
    )

    with caplog.at_level("ERROR"):
        spider.errback(failure)

    assert spider.stats["errors"] == 1
    assert "boom" in caplog.text


def test_spider_parse_enqueues_links(spider):
    """Parse schedules new requests respecting visited set."""
    from types import SimpleNamespace

    class DummyCrawler(SimpleNamespace):
        def __init__(self):
            super().__init__(
                process_response=lambda resp, sp: None,
                manifest_writer=SimpleNamespace(write_graph_entry=lambda entry: None),
            )

    spider.crawler_instance = DummyCrawler()

    html = """
    <html>
      <body>
        <a href="https://example.com/page1">One</a>
        <a href="https://example.com/page2">Two</a>
      </body>
    </html>
    """
    request = Request("https://example.com/root")
    request.meta["depth"] = 0
    response = HtmlResponse(
        url="https://example.com/root",
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=request,
    )
    from webarc.utils.url import canonicalize_url

    spider.visited_urls.add(canonicalize_url("https://example.com/page1"))

    results = list(spider.parse(response))

    assert len(results) == 1
    assert isinstance(results[0], Request)
    assert results[0].url == "https://example.com/page2"
    assert results[0].meta["depth"] == 1


def test_spider_start_requests_extra_seed(config):
    """Additional seed URLs are yielded at depth zero."""
    spider = WebArcSpider(
        seed_url="https://example.com/root",
        config=config,
        allowed_domain="example.com",
        max_depth=1,
        extra_seed_urls=["https://example.com/extra"],
    )
    requests = list(spider.start_requests())
    urls = {req.url for req in requests}
    assert urls == {"https://example.com/root", "https://example.com/extra"}
    for req in requests:
        assert req.meta["depth"] == 0


def test_spider_parse_version_lock(monkeypatch, config):
    """Version lock permits only matching URLs."""
    spider = WebArcSpider(
        seed_url="https://example.com/appd/25.10.0/root",
        config=config,
        allowed_domain="example.com",
        max_depth=2,
        version_lock="/25.10.0/",
    )

    class DummyCrawler:
        def __init__(self):
            self.manifest_writer = SimpleNamespace(write_graph_entry=lambda entry: None)

        def process_response(self, response, spider):
            return None

    spider.crawler_instance = DummyCrawler()

    html = """
    <html>
      <body>
        <a href="https://example.com/appd/25.10.0/keep">Keep</a>
        <a href="https://example.com/appd/24.3.0/skip">Skip</a>
      </body>
    </html>
    """
    request = Request("https://example.com/appd/25.10.0/root")
    request.meta["depth"] = 0
    response = HtmlResponse(
        url=request.url,
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=request,
    )

    results = list(spider.parse(response))
    assert len(results) == 1
    assert results[0].url.endswith("/keep")
    assert spider.stats["pages_skipped"] == 1


def test_spider_param_explosion_blocks(monkeypatch, config):
    """Parameter explosion detector stops URL when enforcing."""
    spider = WebArcSpider(
        seed_url="https://example.com/root",
        config=config,
        allowed_domain="example.com",
        max_depth=2,
    )
    spider.config.safety.mode = "enforce"
    spider.crawler_instance = SimpleNamespace(
        process_response=lambda resp, sp: None,
        manifest_writer=SimpleNamespace(write_graph_entry=lambda entry: None),
    )

    monkeypatch.setattr(
        spider.param_detector,
        "check_url",
        lambda url: (True, "too many params"),
    )

    html = '<html><body><a href="https://example.com/page?x=1&y=2">Link</a></body></html>'
    request = Request("https://example.com/root")
    request.meta["depth"] = 0
    response = HtmlResponse(
        url="https://example.com/root",
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=request,
    )

    results = list(spider.parse(response))
    assert results == []
    assert spider.stats["pages_skipped"] == 1


def test_spider_random_segment_blocks(monkeypatch, config):
    """Random segment detection prevents following suspicious links."""
    spider = WebArcSpider(
        seed_url="https://example.com/root",
        config=config,
        allowed_domain="example.com",
        max_depth=2,
    )
    spider.config.safety.mode = "enforce"
    spider.crawler_instance = SimpleNamespace(
        process_response=lambda resp, sp: None,
        manifest_writer=SimpleNamespace(write_graph_entry=lambda entry: None),
    )

    monkeypatch.setattr(
        "webarc.crawler.spider.check_url_for_random_segments",
        lambda url, threshold: (True, ["abcdef"]),
    )

    html = '<html><body><a href="https://example.com/random/abcdef">Link</a></body></html>'
    request = Request("https://example.com/root")
    request.meta["depth"] = 0
    response = HtmlResponse(
        url="https://example.com/root",
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=request,
    )

    results = list(spider.parse(response))
    assert results == []
    assert spider.stats["pages_skipped"] == 1


def test_spider_pagination_limit(monkeypatch, config):
    """Pagination detector halts further crawling when limit reached."""
    spider = WebArcSpider(
        seed_url="https://example.com/root",
        config=config,
        allowed_domain="example.com",
        max_depth=2,
    )
    spider.crawler_instance = SimpleNamespace(
        process_response=lambda resp, sp: None,
        manifest_writer=SimpleNamespace(write_graph_entry=lambda entry: None),
    )

    monkeypatch.setattr(
        spider.pagination_detector,
        "should_follow",
        lambda url: False,
    )

    html = '<html><body><a href="https://example.com/page?page=2">Page 2</a></body></html>'
    request = Request("https://example.com/root")
    request.meta["depth"] = 0
    response = HtmlResponse(
        url="https://example.com/root",
        body=html.encode("utf-8"),
        encoding="utf-8",
        request=request,
    )

    results = list(spider.parse(response))
    assert results == []
    assert spider.stats["pages_skipped"] == 1
