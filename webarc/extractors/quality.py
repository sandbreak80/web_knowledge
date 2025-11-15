"""Content quality metrics and evaluation."""

import logging
from typing import Tuple, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class ContentQuality:
    """
    Evaluate page quality and determine if worth extracting.
    """
    
    def __init__(self, html: str, url: str):
        """
        Initialize content quality evaluator.
        
        Args:
            html: HTML content
            url: Page URL
        """
        self.html = html
        self.url = url
        self.soup = BeautifulSoup(html, 'lxml')
        
        # Extract metrics
        self.text = self._extract_text()
        self.word_count = len(self.text.split())
        self.html_length = len(html)
        self.content_density = self._calculate_density()
        self.link_count = len(self.soup.find_all('a'))
        self.paragraph_count = len(self.soup.find_all('p'))
        self.heading_count = len(self.soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']))
        self.table_count = len(self.soup.find_all('table'))
        self.code_block_count = len(self.soup.find_all(['pre', 'code']))
    
    def _calculate_density(self) -> float:
        """
        Content density = (text_length - nav_text) / html_length
        
        Higher density = more content, less boilerplate
        """
        # Estimate navigation text
        nav_elements = self.soup.find_all(['nav', 'header', 'footer', 'aside'])
        nav_text_length = sum(len(el.get_text()) for el in nav_elements)
        
        content_length = len(self.text) - nav_text_length
        
        if self.html_length == 0:
            return 0
        
        density = content_length / self.html_length
        return max(0, min(1, density))  # Clamp to [0, 1]
    
    def _extract_text(self) -> str:
        """Extract visible text."""
        # Remove script and style elements
        for element in self.soup(['script', 'style', 'noscript']):
            element.decompose()
        
        return self.soup.get_text(separator=' ', strip=True)
    
    def is_acceptable(
        self,
        min_content_density: float = 0.3,
        min_content_length: int = 100,
        min_word_count: int = 50,
        max_nav_link_ratio: float = 0.5,
        min_paragraph_count: int = 1,
        require_heading: bool = True
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if page meets quality thresholds.
        
        Args:
            min_content_density: Minimum content density
            min_content_length: Minimum character count
            min_word_count: Minimum word count
            max_nav_link_ratio: Maximum link-to-word ratio
            min_paragraph_count: Minimum paragraph count
            require_heading: Whether headings are required
        
        Returns:
            Tuple of (is_acceptable, reason_if_not)
        """
        # Content density check
        if self.content_density < min_content_density:
            return False, f"Low content density: {self.content_density:.2f}"
        
        # Word count check
        if self.word_count < min_word_count:
            return False, f"Low word count: {self.word_count}"
        
        # Character count check
        if len(self.text) < min_content_length:
            return False, f"Low character count: {len(self.text)}"
        
        # Link-to-text ratio (detect link farms)
        if self.word_count > 0:
            link_ratio = self.link_count / self.word_count
            if link_ratio > max_nav_link_ratio:
                return False, f"High link ratio: {link_ratio:.2f} (link farm?)"
        
        # Must have headings (structural requirement)
        if require_heading and self.heading_count == 0:
            return False, "No headings found"
        
        # Must have paragraphs
        if self.paragraph_count < min_paragraph_count:
            return False, f"Insufficient paragraphs: {self.paragraph_count}"
        
        # Check for "Page Not Found" indicators (only if quality checks enabled)
        # Skip these checks if all thresholds are at minimum (quality checks disabled)
        if not (min_content_density == 0.0 and min_content_length == 0 and min_word_count == 0):
            title = self.soup.find('title')
            if title and any(indicator in title.text.lower() for indicator in ['404', 'not found', 'error']):
                return False, "404 or error page detected"
            
            # Check for paywall indicators
            paywall_indicators = ['subscribe now', 'premium content', 'paid subscribers', 'paywall']
            if any(indicator in self.text.lower() for indicator in paywall_indicators):
                return False, "Paywall detected"
            
            # Check for CAPTCHA
            if 'captcha' in self.text.lower() or self.soup.find(class_=lambda x: x and 'captcha' in x.lower()):
                return False, "CAPTCHA detected"
        
        return True, None
