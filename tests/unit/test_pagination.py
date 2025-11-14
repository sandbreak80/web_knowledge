"""Unit tests for pagination detection."""

from webarc.safety.pagination import PaginationDetector


def test_pagination_detection():
    """Test pagination detection."""
    detector = PaginationDetector()
    
    url = "http://example.com/page?page=2"
    is_paginated, base = detector.is_pagination(url)
    assert is_paginated is True
    assert base is not None


def test_pagination_limit():
    """Test pagination limit enforcement."""
    detector = PaginationDetector(max_pagination_depth=3)
    
    # First few should pass
    assert detector.should_follow("http://example.com/page?page=1") is True
    assert detector.should_follow("http://example.com/page?page=2") is True
    assert detector.should_follow("http://example.com/page?page=3") is True
    
    # Should hit limit
    assert detector.should_follow("http://example.com/page?page=4") is False


def test_non_paginated_urls():
    """Test that non-paginated URLs always pass."""
    detector = PaginationDetector(max_pagination_depth=1)
    
    url = "http://example.com/article"
    assert detector.should_follow(url) is True
