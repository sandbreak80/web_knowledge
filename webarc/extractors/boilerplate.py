"""Boilerplate removal using readability-lxml."""

import logging
from typing import Optional
from readability import Document

logger = logging.getLogger(__name__)


def extract_main_content(html: str, url: str) -> Optional[str]:
    """
    Extract main content from HTML using readability-lxml.
    
    Args:
        html: HTML content
        url: Source URL
    
    Returns:
        Extracted HTML content, or None if extraction failed
    """
    try:
        doc = Document(html)
        content_html = doc.summary()
        return content_html
    except Exception as e:
        logger.warning(f"Failed to extract content from {url}: {e}")
        return None
