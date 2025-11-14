"""Adapter router for selecting appropriate adapter."""

import logging
from typing import List

from webarc.adapters.base import SiteAdapter
from webarc.adapters.confluence import ConfluenceAdapter
from webarc.adapters.mkdocs import MkDocsAdapter
from webarc.adapters.sphinx import SphinxAdapter
from webarc.adapters.generic import GenericAdapter
from webarc.adapters.news import NewsAdapter
from webarc.adapters.reddit import RedditAdapter
from webarc.adapters.squarespace import SquarespaceAdapter
from webarc.config.schema import WebArcConfig

logger = logging.getLogger(__name__)


class AdapterRouter:
    """
    Route pages to appropriate adapter.
    """
    
    def __init__(self, config: WebArcConfig):
        """
        Initialize adapter router.
        
        Args:
            config: WebArc configuration
        """
        self.config = config
        self.adapters: List[SiteAdapter] = [
            ConfluenceAdapter(config),
            MkDocsAdapter(config),
            SphinxAdapter(config),
            NewsAdapter(config),
            RedditAdapter(config),
            SquarespaceAdapter(config),
            GenericAdapter(config),  # Fallback
        ]
    
    def get_adapter(self, url: str, html: str) -> SiteAdapter:
        """
        Select best adapter for this page.
        
        Args:
            url: Page URL
            html: HTML content
        
        Returns:
            SiteAdapter instance
        """
        # Check for explicit adapter override
        if hasattr(self.config, 'force_adapter') and self.config.force_adapter:
            adapter_name = self.config.force_adapter.lower()
            for adapter in self.adapters:
                if adapter.__class__.__name__.lower().startswith(adapter_name):
                    logger.debug(f"Using forced adapter: {adapter.__class__.__name__}")
                    return adapter
        
        # Try each adapter's matches() method
        for adapter in self.adapters:
            if adapter.matches(url, html):
                logger.debug(f"Using {adapter.__class__.__name__} for {url}")
                return adapter
        
        # Fallback to generic (should always match)
        return self.adapters[-1]
