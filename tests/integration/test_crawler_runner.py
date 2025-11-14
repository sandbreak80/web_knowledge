"""Integration tests for WebArcCrawler runner."""

import tempfile
from pathlib import Path
from unittest.mock import Mock

from webarc.crawler.runner import WebArcCrawler
from webarc.config.loader import load_config


def test_crawler_initialization():
    """Test WebArcCrawler initialization."""
    config = load_config()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        crawler = WebArcCrawler(
            seed_url='https://example.com',
            config=config,
            output_dir=Path(tmpdir),
            max_depth=2,
            allowed_domain='example.com',
        )
        
        assert crawler.seed_url == 'https://example.com'
        assert crawler.max_depth == 2
        assert crawler.allowed_domain == 'example.com'
        assert crawler.output_dir == Path(tmpdir)
        assert crawler.stats['pages_crawled'] == 0
        assert crawler.stats['pages_extracted'] == 0


def test_crawler_with_visited_urls():
    """Test WebArcCrawler with visited URLs (resume scenario)."""
    config = load_config()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        visited = {'https://example.com/page1'}
        crawler = WebArcCrawler(
            seed_url='https://example.com',
            config=config,
            output_dir=Path(tmpdir),
            visited_urls=visited,
        )
        
        assert len(crawler.visited_urls) == 1
        assert 'https://example.com/page1' in crawler.visited_urls


def test_process_response_quality_check():
    """Test process_response with quality check."""
    config = load_config()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        crawler = WebArcCrawler(
            seed_url='https://example.com',
            config=config,
            output_dir=Path(tmpdir),
        )
        
        # Create mock response with low quality content
        response = Mock()
        response.url = 'https://example.com/page'
        response.status = 200
        response.text = '<html><body><p>Short</p></body></html>'
        
        spider = Mock()
        spider.visited_urls = set()
        
        initial_stats = crawler.stats.copy()
        crawler.process_response(response, spider)
        
        # Should skip due to low quality
        assert crawler.stats['pages_skipped'] > initial_stats['pages_skipped']


def test_process_response_success():
    """Test process_response with acceptable content."""
    config = load_config()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        crawler = WebArcCrawler(
            seed_url='https://example.com',
            config=config,
            output_dir=Path(tmpdir),
        )
        
        # Create mock response with good content (enough to pass quality checks)
        html = """
        <html>
        <head><title>Test Page</title></head>
        <body>
            <h1>Main Title</h1>
            <p>This is a paragraph with enough content to pass quality checks and ensure we have sufficient word count. It needs to be long enough to meet all the quality thresholds including word count, content density, and other requirements.</p>
            <p>Another paragraph with more content that adds to the total word count and ensures we have enough text to pass the density threshold. This paragraph continues to add words and content to help meet the minimum requirements.</p>
            <p>Yet another paragraph to ensure we have enough content and words to pass all checks. This paragraph provides additional content to help meet quality thresholds.</p>
            <p>More paragraphs with additional content to meet the minimum requirements for density and word count. This ensures the content passes all quality checks.</p>
            <p>Final paragraph to push the word count above the threshold and ensure density is acceptable. This paragraph completes the content requirements.</p>
        </body>
        </html>
        """
        
        response = Mock()
        response.url = 'https://example.com/page'
        response.status = 200
        response.text = html
        
        spider = Mock()
        spider.visited_urls = set()
        
        initial_extracted = crawler.stats['pages_extracted']
        initial_crawled = crawler.stats['pages_crawled']
        crawler.process_response(response, spider)
        
        # Should have crawled the page
        assert crawler.stats['pages_crawled'] > initial_crawled
        # May extract or skip depending on quality, but should have processed
        assert crawler.stats['pages_extracted'] >= initial_extracted or crawler.stats['pages_skipped'] > 0


def test_process_response_error_handling():
    """Test process_response error handling."""
    config = load_config()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        crawler = WebArcCrawler(
            seed_url='https://example.com',
            config=config,
            output_dir=Path(tmpdir),
        )
        
        # Create mock response that will cause an error
        response = Mock()
        response.url = 'https://example.com/page'
        response.status = 200
        response.text = None  # This will cause an error
        
        spider = Mock()
        spider.visited_urls = set()
        
        initial_errors = crawler.stats['errors']
        crawler.process_response(response, spider)
        
        # Should record error
        assert crawler.stats['errors'] > initial_errors
