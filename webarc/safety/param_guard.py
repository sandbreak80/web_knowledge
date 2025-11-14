"""Parameter explosion detection for safety guards."""

from urllib.parse import urlparse, parse_qs
from typing import Set, Dict, Optional


class ParamExplosionDetector:
    """
    Detect combinatorial query parameter patterns.
    
    Example: ?color=red&size=small → 100+ URL variations
    """
    
    def __init__(self, max_query_params: int = 10, max_unique_urls: int = 1000):
        """
        Initialize parameter explosion detector.
        
        Args:
            max_query_params: Maximum query parameters before warning
            max_unique_urls: Maximum unique URLs per domain before explosion detected
        """
        self.max_query_params = max_query_params
        self.max_unique_urls = max_unique_urls
        self.url_patterns: Set[str] = set()
        self.param_combinations: Dict[str, Set[str]] = {}
        self.unique_url_count = 0
        self.domain_patterns: Dict[str, int] = {}
    
    def check_url(self, url: str) -> tuple[bool, Optional[str]]:
        """
        Check if URL indicates parameter explosion.
        
        Args:
            url: URL to check
        
        Returns:
            Tuple of (is_explosion, reason_if_yes)
        """
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Extract parameter keys (ignore values)
        if not parsed.query:
            return False, None
        
        params = parse_qs(parsed.query)
        param_keys = frozenset(params.keys())
        
        # Check parameter count
        if len(param_keys) > self.max_query_params:
            return True, f"Too many query parameters: {len(param_keys)} > {self.max_query_params}"
        
        # Track parameter combinations per domain
        # pattern_key = f"{parsed.path}:{sorted(param_keys)}"  # For future use
        
        if domain not in self.domain_patterns:
            self.domain_patterns[domain] = 0
        
        self.domain_patterns[domain] += 1
        self.unique_url_count += 1
        
        # Check if we've seen too many unique URLs for this domain
        if self.domain_patterns[domain] > self.max_unique_urls:
            return True, f"Parameter explosion detected: {self.domain_patterns[domain]} unique URLs for {domain}"
        
        return False, None
    
    def reset(self):
        """Reset detector state."""
        self.url_patterns.clear()
        self.param_combinations.clear()
        self.unique_url_count = 0
        self.domain_patterns.clear()
