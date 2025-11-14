"""Render router for static vs JavaScript rendering decision."""

import logging
from typing import Set
from urllib.parse import urlparse

from webarc.config.schema import WebArcConfig

logger = logging.getLogger(__name__)


class RenderRouter:
    """
    Decide whether to use static HTML or JavaScript rendering.
    """
    
    def __init__(self, config: WebArcConfig):
        """
        Initialize render router.
        
        Args:
            config: WebArc configuration
        """
        self.config = config
        self.js_needed_cache: Set[str] = set()  # Domains that needed JS
    
    def check_js_needed(self, html: str, url: str) -> bool:
        """
        Detect if JavaScript rendering is required.
        
        Args:
            html: HTML content to check
            url: URL of the page
        
        Returns:
            True if JavaScript rendering is needed
        """
        # Check if force_js is enabled
        if self.config.render.force_js:
            return True
        
        # Check domain cache (previously needed JS?)
        domain = self._extract_domain(url)
        if domain in self.js_needed_cache:
            return True
        
        # Check content length
        text = self._extract_text(html)
        min_length = 500  # Default minimum content length
        if len(text) < min_length:
            logger.debug(f"Low content ({len(text)} chars), trying JS")
            return True
        
        # Check for JS framework indicators
        for trigger in self.config.render.js_detection_triggers:
            if trigger in html:
                logger.debug(f"JS trigger detected: {trigger}")
                return True
        
        # Check for empty content containers
        if '<div id="root"></div>' in html or '<div id="app"></div>' in html:
            return True
        
        # Check noscript warnings
        if '<noscript>' in html.lower() and 'javascript' in html.lower():
            noscript_text = html.lower()
            if 'you need javascript' in noscript_text or 'enable javascript' in noscript_text:
                return True
        
        return False
    
    def mark_domain_js_needed(self, url: str):
        """
        Mark domain as requiring JavaScript rendering.
        
        Args:
            url: URL to extract domain from
        """
        domain = self._extract_domain(url)
        self.js_needed_cache.add(domain)
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        parsed = urlparse(url)
        return parsed.netloc.lower()
    
    def _extract_text(self, html: str) -> str:
        """
        Extract visible text from HTML (simple version).
        
        Args:
            html: HTML content
        
        Returns:
            Extracted text
        """
        # Simple text extraction - remove script and style tags
        import re
        # Remove script tags
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove style tags
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL | re.IGNORECASE)
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', html)
        # Normalize whitespace
        text = ' '.join(text.split())
        return text
