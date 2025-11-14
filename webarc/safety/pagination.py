"""Pagination detection and limiting."""

import re
from urllib.parse import urlparse
from typing import Optional, Tuple, Dict, List


class PaginationDetector:
    """
    Detect and limit pagination chains.
    """
    
    def __init__(self, max_pagination_depth: int = 50, pagination_keywords: Optional[List[str]] = None):
        """
        Initialize pagination detector.
        
        Args:
            max_pagination_depth: Maximum pages to follow per pagination chain
            pagination_keywords: Keywords indicating pagination parameters
        """
        self.max_pagination_depth = max_pagination_depth
        self.pagination_keywords = pagination_keywords or [
            "page", "offset", "start", "limit", "skip"
        ]
        self.pagination_chains: Dict[str, List[str]] = {}
        self.pattern_counters: Dict[str, int] = {}
    
    def is_pagination(self, url: str) -> Tuple[bool, Optional[str]]:
        """
        Check if URL is part of a pagination sequence.
        
        Args:
            url: URL to check
        
        Returns:
            Tuple of (is_pagination, base_pattern)
        """
        parsed = urlparse(url)
        
        # Check query parameters for pagination keywords
        if parsed.query:
            params = parsed.query.lower()
            for keyword in self.pagination_keywords:
                if keyword in params:
                    # Extract base pattern (remove pagination param)
                    base_pattern = re.sub(
                        rf'[?&]{keyword}=\d+',
                        '',
                        url,
                        flags=re.IGNORECASE
                    )
                    return True, base_pattern
        
        # Check for /page/N pattern
        page_number_pattern = r'/page/\d+|/p\d+|/\d+/?$'
        if re.search(page_number_pattern, url):
            base = re.sub(page_number_pattern, '', url)
            return True, base
        
        return False, None
    
    def should_follow(self, url: str) -> bool:
        """
        Check if we should continue following pagination.
        
        Args:
            url: URL to check
        
        Returns:
            True if should follow, False if limit reached
        """
        is_paginated, base = self.is_pagination(url)
        
        if not is_paginated or base is None:
            return True
        
        # Track pagination depth
        if base not in self.pattern_counters:
            self.pattern_counters[base] = 0
        
        self.pattern_counters[base] += 1
        
        if self.pattern_counters[base] > self.max_pagination_depth:
            return False
        
        return True
    
    def reset(self):
        """Reset detector state."""
        self.pagination_chains.clear()
        self.pattern_counters.clear()
