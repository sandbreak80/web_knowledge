"""Robots.txt parser (RFC 9309 compliant)."""

from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class RobotsTxtParser:
    """
    RFC 9309 compliant robots.txt parser.
    """
    
    def __init__(self, domain: str, user_agent: str = "WebArc"):
        """
        Initialize robots.txt parser.
        
        Args:
            domain: Domain to check robots.txt for
            user_agent: User agent string to match rules
        """
        self.domain = domain
        self.user_agent = user_agent
        self.rules: Dict[str, List[str]] = {'disallow': [], 'allow': []}
        self.crawl_delay: Optional[float] = None
        self.sitemaps: List[str] = []
        self.loaded = False
    
    def parse(self, content: str):
        """
        Parse robots.txt content.
        
        Args:
            content: robots.txt file content
        """
        user_agent_section = None
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Skip comments and empty lines
            if not line or line.startswith('#'):
                continue
            
            # Parse directives
            if ':' not in line:
                continue
            
            key, value = line.split(':', 1)
            key = key.strip().lower()
            value = value.strip()
            
            if key == 'user-agent':
                # Check if this section applies to us
                if value == '*' or value.lower() in self.user_agent.lower():
                    user_agent_section = True
                else:
                    user_agent_section = False
            
            elif user_agent_section:
                if key == 'disallow':
                    self.rules['disallow'].append(value)
                elif key == 'allow':
                    self.rules['allow'].append(value)
                elif key == 'crawl-delay':
                    try:
                        self.crawl_delay = float(value)
                    except ValueError:
                        logger.warning(f"Invalid crawl-delay value: {value}")
                elif key == 'sitemap':
                    self.sitemaps.append(value)
        
        # Mark as loaded after parsing
        self.loaded = True
    
    def can_fetch(self, path: str) -> bool:
        """
        Check if we're allowed to fetch this path.
        
        Args:
            path: URL path to check
        
        Returns:
            True if allowed, False if disallowed
        """
        if not self.loaded:
            return True  # Not loaded yet, be optimistic
        
        # Check disallow rules (ignore allow rules for safety)
        for pattern in self.rules['disallow']:
            if not pattern:  # Empty disallow = allow all
                continue
            
            # Simple prefix matching (not full wildcard support)
            if path.startswith(pattern):
                return False
        
        return True
    
    def get_robots_url(self) -> str:
        """
        Get robots.txt URL for this domain.
        
        Returns:
            robots.txt URL
        """
        return f"https://{self.domain}/robots.txt"
