"""Unit tests for content quality evaluation."""

from webarc.extractors.quality import ContentQuality


def test_content_quality_acceptable():
    """Test that good quality content passes."""
    html = """
    <html>
    <head><title>Test Page</title></head>
    <body>
        <h1>Main Title</h1>
        <p>This is a paragraph with enough content to pass quality checks and ensure we have sufficient word count.</p>
        <p>Another paragraph with more content that adds to the total word count.</p>
        <p>Yet another paragraph to ensure we have enough content and words.</p>
        <p>More paragraphs with additional content to meet the minimum requirements.</p>
        <p>Final paragraph to push the word count above the threshold.</p>
    </body>
    </html>
    """
    
    quality = ContentQuality(html, "https://example.com/page")
    is_acceptable, reason = quality.is_acceptable(min_word_count=30)
    
    assert is_acceptable is True
    assert quality.word_count > 30
    assert quality.heading_count > 0


def test_content_quality_low_density():
    """Test that low density content fails."""
    html = """
    <html>
    <body>
        <nav>Navigation Navigation Navigation</nav>
        <div style="display:none">Hidden Hidden Hidden</div>
        <p>Short</p>
    </body>
    </html>
    """
    
    quality = ContentQuality(html, "https://example.com/page")
    is_acceptable, reason = quality.is_acceptable(min_content_density=0.5)
    
    assert is_acceptable is False
    assert "density" in reason.lower()


def test_content_quality_no_heading():
    """Test that content without headings fails when required."""
    html = """
    <html>
    <body>
        <p>This is a paragraph with enough content to pass density checks. It has sufficient words and characters to meet the minimum requirements for content density and word count.</p>
        <p>Another paragraph with more content that adds to the total word count and ensures we have enough text to pass the density threshold.</p>
        <p>Yet another paragraph to ensure we have enough content and words to pass all checks except the heading requirement.</p>
        <p>More paragraphs with additional content to meet the minimum requirements for density and word count.</p>
        <p>Final paragraph to push the word count above the threshold and ensure density is acceptable.</p>
    </body>
    </html>
    """
    
    quality = ContentQuality(html, "https://example.com/page")
    is_acceptable, reason = quality.is_acceptable(
        require_heading=True,
        min_content_density=0.1,  # Lower threshold to ensure density passes
        min_word_count=20  # Lower threshold to ensure word count passes
    )
    
    assert is_acceptable is False
    assert "heading" in reason.lower()
