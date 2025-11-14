"""Integration coverage for safety utility modules."""

from webarc.safety.domain_fence import (
    extract_registered_domain,
    is_same_registered_domain,
    validate_domain_restriction,
)
from webarc.safety.entropy import calculate_entropy, is_random_identifier, check_url_for_random_segments
from webarc.safety.pagination import PaginationDetector


def test_domain_fence_utilities():
    assert extract_registered_domain("sub.example.co.uk") == "example.co.uk"
    assert is_same_registered_domain("https://a.example.com/page", "https://b.example.com/other") is True
    allowed, reason = validate_domain_restriction(
        "https://docs.example.com/path",
        allowed_domain="example.com",
        allowed_prefix="/path",
    )
    assert allowed is True
    allowed, reason = validate_domain_restriction(
        "https://docs.example.com/other",
        allowed_domain="example.com",
        allowed_prefix="/path",
    )
    assert allowed is False
    assert "Path prefix mismatch" in reason


def test_entropy_detection():
    assert calculate_entropy("aaaa") == 0.0
    uuid = "8f4a3b2c1d6e4f9ab3c27e8d9f0a1b2c"
    assert is_random_identifier(uuid) is True
    has_random, segments = check_url_for_random_segments(f"https://example.com/docs/{uuid}/page")
    assert has_random is True
    assert uuid in segments


def test_pagination_detector_limits():
    detector = PaginationDetector(max_pagination_depth=2)
    base = "https://example.com/articles?page="
    assert detector.should_follow(f"{base}1") is True
    assert detector.should_follow(f"{base}2") is True
    assert detector.should_follow(f"{base}3") is False
    detector.reset()
    assert detector.should_follow("https://example.com/blog/page/1") is True

