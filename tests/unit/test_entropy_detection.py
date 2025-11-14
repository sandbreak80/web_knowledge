"""Unit tests for entropy detection."""

from webarc.safety.entropy import calculate_entropy, is_random_identifier, check_url_for_random_segments


def test_uuid_detection():
    """Test UUID detection."""
    assert is_random_identifier("8f4a3b2c-1d6e-4f9a-b3c2-7e8d9f0a1b2c")
    assert is_random_identifier("8f4a3b2c1d6e4f9ab3c27e8d9f0a1b2c")  # No dashes


def test_entropy_calculation():
    """Test entropy calculation."""
    # High entropy (random)
    assert calculate_entropy("aB3dE7fG9hJ2kL4mN6pQ8rS") > 3.5
    
    # Low entropy (repetitive)
    assert calculate_entropy("aaaaaaaaaa") < 1.0
    
    # Medium entropy (normal text)
    assert 2.0 < calculate_entropy("hello-world-page") < 3.5


def test_short_strings_not_flagged():
    """Test that short strings are not flagged."""
    assert not is_random_identifier("a1B2c3")


def test_check_url_for_random_segments():
    """Test URL checking for random segments."""
    url1 = "https://example.com/docs/8f4a3b2c-1d6e-4f9a-b3c2-7e8d9f0a1b2c/page"
    has_random, segments = check_url_for_random_segments(url1)
    assert has_random is True
    assert len(segments) > 0
    
    url2 = "https://example.com/docs/getting-started"
    has_random, segments = check_url_for_random_segments(url2)
    assert has_random is False
