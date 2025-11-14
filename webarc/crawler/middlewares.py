"""Scrapy middlewares for WebArc safety guards."""

import logging
from typing import Optional
from scrapy.http import Request, Response

from webarc.config.schema import WebArcConfig
from webarc.safety.robots import RobotsTxtParser
from webarc.safety.blocklist import check_blocklist

logger = logging.getLogger(__name__)


class DomainFenceMiddleware:
    """
    Middleware to enforce domain restrictions.
    """
    
    def __init__(self, allowed_domain: Optional[str] = None, allowed_prefix: Optional[str] = None):
        """
        Initialize domain fence middleware.
        
        Args:
            allowed_domain: Required domain
            allowed_prefix: Required path prefix
        """
        self.allowed_domain = allowed_domain
        self.allowed_prefix = allowed_prefix
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler settings."""
        allowed_domain = crawler.settings.get('ALLOWED_DOMAIN')
        allowed_prefix = crawler.settings.get('ALLOWED_PREFIX')
        return cls(allowed_domain, allowed_prefix)
    
    def process_request(self, request: Request, spider) -> Optional[Response]:
        """
        Process request and check domain restrictions.
        
        Args:
            request: Scrapy Request
            spider: Spider instance
        
        Returns:
            None to continue processing, or Response to stop
        """
        from webarc.safety.domain_fence import validate_domain_restriction
        
        allowed, reason = validate_domain_restriction(
            request.url,
            self.allowed_domain,
            self.allowed_prefix
        )
        
        if not allowed:
            logger.debug(f"Domain fence blocked: {request.url} - {reason}")
            # Return a response that will be ignored
            return Response(request.url, status=403)
        
        return None


class WebArcRobotsTxtMiddleware:
    """
    Custom robots.txt middleware using our parser.
    """
    
    def __init__(self, config: WebArcConfig):
        """
        Initialize robots.txt middleware.
        
        Args:
            config: WebArc configuration
        """
        self.config = config
        self.robots_cache: dict[str, RobotsTxtParser] = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler."""
        config = crawler.settings.get('WEBCARC_CONFIG')
        return cls(config)
    
    def process_request(self, request: Request, spider) -> Optional[Response]:
        """
        Check robots.txt before processing request.
        
        Args:
            request: Scrapy Request
            spider: Spider instance
        
        Returns:
            None to continue, or Response to block
        """
        if not self.config.safety.respect_robots_txt:
            return None
        
        from urllib.parse import urlparse
        
        parsed = urlparse(request.url)
        domain = parsed.netloc.lower()
        
        # Get or create robots.txt parser for this domain
        if domain not in self.robots_cache:
            parser = RobotsTxtParser(domain, self.config.crawler.user_agent)
            # Note: In real implementation, we'd fetch robots.txt here
            # For now, we'll assume it's allowed if not loaded
            self.robots_cache[domain] = parser
        
        parser = self.robots_cache[domain]
        
        # Check if path is allowed
        if not parser.can_fetch(parsed.path):
            logger.debug(f"Robots.txt blocked: {request.url}")
            return Response(request.url, status=403)
        
        return None


class BlocklistMiddleware:
    """
    Middleware to check domains against blocklist.
    """
    
    def __init__(self, config: WebArcConfig):
        """
        Initialize blocklist middleware.
        
        Args:
            config: WebArc configuration
        """
        self.config = config
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler."""
        config = crawler.settings.get('WEBCARC_CONFIG')
        return cls(config)
    
    def process_request(self, request: Request, spider) -> Optional[Response]:
        """
        Check domain against blocklist.
        
        Args:
            request: Scrapy Request
            spider: Spider instance
        
        Returns:
            None to continue, or Response to block
        """
        if not self.config.safety.use_blocklist:
            return None
        
        from webarc.utils.url import extract_domain
        
        domain = extract_domain(request.url)
        
        if check_blocklist(domain, self.config.safety.blocklist_path):
            logger.warning(f"Domain blocked by blocklist: {domain}")
            return Response(request.url, status=403)
        
        return None
