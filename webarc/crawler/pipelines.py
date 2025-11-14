"""Scrapy pipelines for WebArc crawler."""

import logging
from typing import Optional
from scrapy import Item

logger = logging.getLogger(__name__)


class WebArcPipeline:
    """
    Base pipeline for WebArc processing.
    """
    
    def process_item(self, item: Item, spider) -> Item:
        """
        Process item through pipeline.
        
        Args:
            item: Scrapy Item
            spider: Spider instance
        
        Returns:
            Processed item
        """
        return item


class DuplicateFilterPipeline:
    """
    Pipeline to filter duplicate URLs based on canonical URLs.
    """
    
    def __init__(self):
        """Initialize duplicate filter."""
        self.seen_urls: set[str] = set()
    
    def process_item(self, item: Item, spider) -> Optional[Item]:
        """
        Filter duplicate items.
        
        Args:
            item: Scrapy Item
            spider: Spider instance
        
        Returns:
            Item if not duplicate, None otherwise
        """
        canonical_url = item.get('canonical_url') or item.get('url')
        
        if canonical_url in self.seen_urls:
            logger.debug(f"Duplicate item filtered: {canonical_url}")
            return None
        
        self.seen_urls.add(canonical_url)
        return item
