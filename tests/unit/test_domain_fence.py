"""Unit tests for domain fencing."""

from webarc.safety.domain_fence import (
    extract_domain_from_url,
    validate_domain_restriction
)


def test_extract_domain():
    """Test domain extraction."""
    assert extract_domain_from_url("https://example.com:443/path") == "example.com"
    assert extract_domain_from_url("http://sub.example.com/path") == "sub.example.com"


def test_domain_restriction():
    """Test domain restriction validation."""
    url = "https://example.com/page"
    
    # Should pass with matching domain
    allowed, reason = validate_domain_restriction(url, allowed_domain="example.com")
    assert allowed is True
    
    # Should fail with different domain
    allowed, reason = validate_domain_restriction(url, allowed_domain="other.com")
    assert allowed is False
    assert "Domain mismatch" in reason


def test_prefix_restriction():
    """Test prefix restriction validation."""
    url = "https://example.com/docs/page"
    
    # Should pass with matching prefix
    allowed, reason = validate_domain_restriction(url, allowed_prefix="/docs")
    assert allowed is True
    
    # Should fail with different prefix
    allowed, reason = validate_domain_restriction(url, allowed_prefix="/api")
    assert allowed is False
    assert "Path prefix mismatch" in reason
