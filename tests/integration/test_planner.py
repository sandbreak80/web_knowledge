"""Integration tests for CrawlPlanner."""

from webarc.crawler.planner import CrawlPlanner
from webarc.config.loader import load_config


def test_planner_initialization():
    """Test CrawlPlanner initialization."""
    config = load_config()
    planner = CrawlPlanner(
        seed_url='https://example.com',
        config=config,
        allowed_domain='example.com',
        max_depth=3
    )
    
    assert planner.seed_url == 'https://example.com'
    assert planner.allowed_domain == 'example.com'
    assert planner.max_depth == 3


def test_plan_basic():
    """Test basic plan generation."""
    config = load_config()
    planner = CrawlPlanner(
        seed_url='https://example.com/page',
        config=config,
        allowed_domain='example.com',
        max_depth=2
    )
    
    plan = planner.plan()
    
    assert plan['seed_url'] == 'https://example.com/page'
    assert plan['allowed_domain'] == 'example.com'
    assert plan['max_depth'] == 2
    assert 'sitemap_urls' in plan
    assert 'estimated_pages' in plan


def test_plan_invalid_seed():
    """Test plan with invalid seed URL."""
    config = load_config()
    planner = CrawlPlanner(
        seed_url='https://other.com/page',
        config=config,
        allowed_domain='example.com',
        max_depth=2
    )
    
    plan = planner.plan()
    
    assert 'error' in plan
    assert 'validation failed' in plan['error'].lower()


def test_discover_sitemap():
    """Test sitemap discovery (will return empty if no sitemap found)."""
    config = load_config()
    planner = CrawlPlanner(
        seed_url='https://example.com',
        config=config,
    )
    
    # This will likely return empty list since example.com doesn't have a sitemap
    # But we're testing that the method doesn't crash
    urls = planner._discover_sitemap()
    
    # Should return a list (empty or with URLs)
    assert isinstance(urls, list)


def test_discover_sitemap_not_found():
    """Test sitemap discovery when sitemap doesn't exist."""
    config = load_config()
    planner = CrawlPlanner(
        seed_url='https://nonexistent-domain-12345.com',
        config=config,
    )
    
    # Should handle missing sitemap gracefully
    urls = planner._discover_sitemap()
    
    # Should return empty list when sitemap not found
    assert isinstance(urls, list)
    assert len(urls) == 0


def test_parse_sitemap():
    """Test parsing a sitemap XML (will fail gracefully if URL doesn't exist)."""
    config = load_config()
    planner = CrawlPlanner(
        seed_url='https://example.com',
        config=config,
    )
    
    # This will likely return empty since the URL doesn't exist
    # But we're testing that the method doesn't crash
    urls = planner._parse_sitemap('https://nonexistent-domain-12345.com/sitemap.xml')
    
    # Should return a list (empty or with URLs)
    assert isinstance(urls, list)
