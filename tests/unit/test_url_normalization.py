"""Unit tests for URL normalization."""

from webarc.utils.url import canonicalize_url, extract_domain, is_same_domain


def test_normalize_scheme():
    """Test scheme normalization."""
    # Empty path should get trailing slash
    assert canonicalize_url("HTTP://Example.com") == "http://example.com/"


def test_remove_default_ports():
    """Test default port removal."""
    assert canonicalize_url("http://example.com:80/path") == "http://example.com/path/"
    assert canonicalize_url("https://example.com:443/path") == "https://example.com/path/"


def test_normalize_path():
    """Test path normalization."""
    assert canonicalize_url("http://example.com//double//slash") == "http://example.com/double/slash/"
    # Trailing slash preserved for directories
    assert canonicalize_url("http://example.com/trailing/") == "http://example.com/trailing/"


def test_sort_query_params():
    """Test query parameter sorting."""
    url = "http://example.com/?z=3&a=1&m=2"
    expected = "http://example.com/?a=1&m=2&z=3"
    assert canonicalize_url(url) == expected


def test_remove_tracking_params():
    """Test tracking parameter removal."""
    url = "http://example.com/page?utm_source=google&fbclid=123&id=real"
    # Note: path normalization adds trailing slash, so result includes /
    result = canonicalize_url(url)
    assert "utm_source" not in result
    assert "fbclid" not in result
    assert "id=real" in result


def test_fragment_handling():
    """Test fragment handling."""
    # Default: remove fragments
    assert canonicalize_url("http://example.com/page#section") == "http://example.com/page/"
    
    # With preserve_anchors: keep fragments
    assert canonicalize_url("http://example.com/page#section", preserve_anchors=True) == "http://example.com/page/#section"


def test_percent_decoding():
    """Test percent-encoding decoding."""
    assert canonicalize_url("http://example.com/hello%20world") == "http://example.com/hello world/"


def test_extract_domain():
    """Test domain extraction."""
    assert extract_domain("https://example.com:443/path") == "example.com"
    assert extract_domain("http://sub.example.com/path") == "sub.example.com"


def test_is_same_domain():
    """Test same domain check."""
    assert is_same_domain("http://example.com/page1", "https://example.com/page2") is True
    assert is_same_domain("http://example.com/page1", "http://other.com/page2") is False
