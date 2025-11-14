"""Unit tests for render router."""

import pytest
from webarc.render.router import RenderRouter
from webarc.config.loader import load_config


@pytest.fixture
def config():
    """Load test configuration."""
    return load_config()


@pytest.fixture
def router(config):
    """Create render router instance."""
    return RenderRouter(config)


def test_render_router_initialization(router):
    """Test render router initialization."""
    assert router is not None
    assert router.js_needed_cache == set()


def test_check_js_needed_static_content(router):
    """Test JS detection with static HTML."""
    # Create HTML with enough text content (>500 chars after extraction)
    long_text = " ".join(["This is a long paragraph with enough content to pass the minimum length check."] * 20)
    html = f"""
    <html>
    <body>
        <h1>Title</h1>
        <p>{long_text}</p>
        <p>It contains multiple sentences and should be detected as static content that doesn't 
        require JavaScript rendering. The content is substantial and meaningful.</p>
    </body>
    </html>
    """
    
    assert router.check_js_needed(html, "https://example.com/page") is False


def test_check_js_needed_js_framework(router):
    """Test JS detection with React/Vue indicators."""
    html = """
    <html>
    <body>
        <div id="root"></div>
        <script>React.render(...)</script>
    </body>
    </html>
    """
    
    assert router.check_js_needed(html, "https://example.com/page") is True


def test_check_js_needed_low_content(router):
    """Test JS detection with low content."""
    html = """
    <html>
    <body>
        <p>Short</p>
    </body>
    </html>
    """
    
    assert router.check_js_needed(html, "https://example.com/page") is True


def test_check_js_needed_force_js(config):
    """Test force JS mode."""
    config.render.force_js = True
    router = RenderRouter(config)
    
    html = "<html><body>Content</body></html>"
    assert router.check_js_needed(html, "https://example.com/page") is True


def test_mark_domain_js_needed(router):
    """Test marking domain as needing JS."""
    router.mark_domain_js_needed("https://example.com/page")
    assert "example.com" in router.js_needed_cache
    
    # Check that subsequent checks return True
    html = "<html><body>Content</body></html>"
    assert router.check_js_needed(html, "https://example.com/other") is True


def test_extract_domain(router):
    """Test domain extraction."""
    domain = router._extract_domain("https://example.com:8080/path?query=value")
    assert domain == "example.com:8080"


def test_extract_text(router):
    """Test text extraction from HTML."""
    html = """
    <html>
    <head><style>body { color: red; }</style></head>
    <body>
        <script>console.log('test');</script>
        <h1>Title</h1>
        <p>Content paragraph</p>
    </body>
    </html>
    """
    
    text = router._extract_text(html)
    assert "Title" in text
    assert "Content paragraph" in text
    assert "console.log" not in text
    assert "color: red" not in text
