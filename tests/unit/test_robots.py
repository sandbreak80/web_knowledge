"""Unit tests for robots.txt parser."""

from webarc.safety.robots import RobotsTxtParser


def test_parse_robots_txt():
    """Test parsing robots.txt content."""
    parser = RobotsTxtParser("example.com", "WebArc")
    
    content = """
    User-agent: *
    Disallow: /admin/
    Disallow: /private/
    Allow: /public/
    Crawl-delay: 2
    Sitemap: https://example.com/sitemap.xml
    """
    
    parser.parse(content)
    assert parser.loaded is True
    assert len(parser.rules['disallow']) == 2
    assert '/admin/' in parser.rules['disallow']
    assert parser.crawl_delay == 2.0
    assert len(parser.sitemaps) == 1


def test_can_fetch():
    """Test can_fetch method."""
    parser = RobotsTxtParser("example.com", "WebArc")
    
    content = """
    User-agent: *
    Disallow: /admin/
    """
    
    parser.parse(content)
    
    assert parser.can_fetch("/page") is True
    assert parser.can_fetch("/admin/") is False
    assert parser.can_fetch("/admin/users") is False


def test_empty_disallow_allows_all():
    """Test that empty disallow allows all."""
    parser = RobotsTxtParser("example.com", "WebArc")
    
    content = """
    User-agent: *
    Disallow:
    """
    
    parser.parse(content)
    assert parser.can_fetch("/anything") is True
