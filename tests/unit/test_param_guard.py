"""Unit tests for parameter explosion detection."""

from webarc.safety.param_guard import ParamExplosionDetector


def test_param_count_check():
    """Test parameter count checking."""
    detector = ParamExplosionDetector(max_query_params=5)
    
    url1 = "http://example.com/page?a=1&b=2&c=3&d=4&e=5&f=6"
    is_explosion, reason = detector.check_url(url1)
    assert is_explosion is True
    assert "Too many query parameters" in reason


def test_normal_param_count():
    """Test that normal parameter counts pass."""
    detector = ParamExplosionDetector(max_query_params=10)
    
    url = "http://example.com/page?a=1&b=2&c=3"
    is_explosion, reason = detector.check_url(url)
    assert is_explosion is False


def test_no_query_params():
    """Test URLs without query parameters."""
    detector = ParamExplosionDetector()
    
    url = "http://example.com/page"
    is_explosion, reason = detector.check_url(url)
    assert is_explosion is False
