"""Unit tests for Scrapy pipelines."""

from scrapy import Item, Field
from webarc.crawler.pipelines import WebArcPipeline, DuplicateFilterPipeline


class TestItem(Item):
    """Test item with fields."""
    url = Field()
    title = Field()
    canonical_url = Field()


def test_webarc_pipeline_process_item():
    """Test WebArcPipeline processes items."""
    pipeline = WebArcPipeline()
    
    item = TestItem()
    item['url'] = 'https://example.com/page'
    item['title'] = 'Test Page'
    
    result = pipeline.process_item(item, None)
    
    assert result is not None
    assert result['url'] == 'https://example.com/page'
    assert result['title'] == 'Test Page'


def test_duplicate_filter_pipeline_initialization():
    """Test DuplicateFilterPipeline initialization."""
    pipeline = DuplicateFilterPipeline()
    assert pipeline.seen_urls == set()


def test_duplicate_filter_pipeline_unique_items():
    """Test duplicate filter with unique items."""
    pipeline = DuplicateFilterPipeline()
    
    item1 = TestItem()
    item1['url'] = 'https://example.com/page1'
    item1['canonical_url'] = 'https://example.com/page1'
    
    item2 = TestItem()
    item2['url'] = 'https://example.com/page2'
    item2['canonical_url'] = 'https://example.com/page2'
    
    result1 = pipeline.process_item(item1, None)
    result2 = pipeline.process_item(item2, None)
    
    assert result1 is not None
    assert result2 is not None
    assert result1['url'] == 'https://example.com/page1'
    assert result2['url'] == 'https://example.com/page2'


def test_duplicate_filter_pipeline_duplicates():
    """Test duplicate filter filters duplicates."""
    pipeline = DuplicateFilterPipeline()
    
    item1 = TestItem()
    item1['url'] = 'https://example.com/page'
    item1['canonical_url'] = 'https://example.com/page'
    
    item2 = TestItem()
    item2['url'] = 'https://example.com/page'
    item2['canonical_url'] = 'https://example.com/page'
    
    result1 = pipeline.process_item(item1, None)
    result2 = pipeline.process_item(item2, None)
    
    assert result1 is not None
    assert result2 is None  # Duplicate filtered


def test_duplicate_filter_pipeline_fallback_to_url():
    """Test duplicate filter uses url if canonical_url missing."""
    pipeline = DuplicateFilterPipeline()
    
    item1 = TestItem()
    item1['url'] = 'https://example.com/page'
    
    item2 = TestItem()
    item2['url'] = 'https://example.com/page'
    
    result1 = pipeline.process_item(item1, None)
    result2 = pipeline.process_item(item2, None)
    
    assert result1 is not None
    assert result2 is None  # Duplicate filtered
