"""Scrapy spider for WebArc crawler."""

import logging
from typing import Optional, Set
from urllib.parse import urljoin

import scrapy
from scrapy.http import Response, Request

from webarc.config.loader import load_config
from webarc.config.schema import WebArcConfig
from webarc.utils.url import canonicalize_url
from webarc.safety.domain_fence import validate_domain_restriction
from webarc.safety.entropy import check_url_for_random_segments
from webarc.safety.param_guard import ParamExplosionDetector
from webarc.safety.pagination import PaginationDetector

logger = logging.getLogger(__name__)


class WebArcSpider(scrapy.Spider):
    """
    Main Scrapy spider for WebArc crawler.
    
    Features:
    - Depth-limited crawling
    - Domain fencing
    - Safety guard integration
    - URL canonicalization
    """
    
    name = "webarc"
    
    def __init__(
        self,
        seed_url: str,
        config: Optional[WebArcConfig] = None,
        allowed_domain: Optional[str] = None,
        allowed_prefix: Optional[str] = None,
        max_depth: int = 3,
        visited_urls: Optional[Set[str]] = None,
        version_lock: Optional[str] = None,
        extra_seed_urls: Optional[list[str]] = None,
        *args,
        **kwargs
    ):
        """
        Initialize WebArc spider.
        
        Args:
            seed_url: Starting URL for crawl
            config: WebArc configuration
            allowed_domain: Restrict crawling to this domain
            allowed_prefix: Restrict crawling to URLs with this path prefix
            max_depth: Maximum crawl depth
            visited_urls: Set of already-visited URLs (for resume)
        """
        super().__init__(*args, **kwargs)
        
        self.config = config or load_config()
        self.seed_url = seed_url
        self.allowed_domain = allowed_domain or self.config.allow_domain
        self.allowed_prefix = allowed_prefix or self.config.allow_prefix
        self.max_depth = (
            max_depth if max_depth is not None else self.config.crawler.max_depth
        )
        self.version_lock = version_lock
        self.extra_seed_urls = extra_seed_urls or []
        logger.debug(
            "Initialized WebArcSpider with seed=%s, max_depth=%s, allowed_prefix=%s",
            self.seed_url,
            self.max_depth,
            self.allowed_prefix,
        )
        
        # Track visited URLs (canonicalized)
        self.visited_urls: Set[str] = visited_urls or set()
        
        # Safety guard instances
        self.param_detector = ParamExplosionDetector(
            max_query_params=self.config.safety.max_query_params,
            max_unique_urls=1000
        )
        self.pagination_detector = PaginationDetector(
            max_pagination_depth=self.config.safety.max_pagination_depth,
            pagination_keywords=self.config.safety.pagination_keywords
        )
        
        # Statistics
        self.stats = {
            'pages_crawled': 0,
            'pages_extracted': 0,
            'pages_skipped': 0,
            'errors': 0,
        }
    
    def start_requests(self):
        """Generate initial requests."""
        # Canonicalize seed URL
        canonical_seed = canonicalize_url(self.seed_url)
        
        # Validate domain restriction
        allowed, reason = validate_domain_restriction(
            self.seed_url,
            self.allowed_domain,
            self.allowed_prefix
        )
        
        if not allowed:
            logger.error(f"Seed URL validation failed: {reason}")
            return
        
        self.visited_urls.add(canonical_seed)
        
        yield Request(
            url=self.seed_url,
            callback=self.parse,
            errback=self.errback,
            meta={
                'depth': 0,
                'canonical_url': canonical_seed,
            }
        )

        # STRICT FILTER: Only allow extra_seed_urls that start with the exact seed URL prefix
        seed_prefix = '/'.join(self.seed_url.split('/')[:7])  # Get up to /en
        for extra_url in self.extra_seed_urls:
            if not extra_url.startswith(seed_prefix):
                logger.debug(f"Skipping extra_seed_url {extra_url}: does not start with {seed_prefix}")
                continue
            canonical_extra = canonicalize_url(extra_url)
            if canonical_extra in self.visited_urls:
                continue
            self.visited_urls.add(canonical_extra)
            yield Request(
                url=extra_url,
                callback=self.parse,
                errback=self.errback,
                meta={
                    'depth': 0,
                    'canonical_url': canonical_extra,
            }
        )
    
    def parse(self, response: Response):
        """
        Parse response and extract links.
        
        Args:
            response: Scrapy Response object
        """
        self.stats['pages_crawled'] += 1
        
        depth = response.meta.get('depth', 0)
        
        logger.debug(f"Parsing {response.url} (depth: {depth})")
        
        # Process response through pipeline if crawler instance available
        if hasattr(self, 'crawler_instance') and self.crawler_instance:
            self.crawler_instance.process_response(response, self)
        
        # Check if we've exceeded max depth
        if depth >= self.max_depth:
            logger.debug(f"Max depth reached for {response.url}")
            return
        
        # Extract links from page
        links = self._extract_links(response)
        
        # Process each link
        for link_url in links:
            # Resolve relative URLs
            absolute_url = urljoin(response.url, link_url)
            
            # Skip binary file extensions
            binary_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg', '.pdf', '.zip', '.exe', '.dmg', '.pkg', '.tar', '.gz', '.bz2', '.mp3', '.mp4', '.avi', '.mov', '.webm'}
            if any(absolute_url.lower().endswith(ext) for ext in binary_extensions):
                logger.debug(f"Skipping binary file link: {absolute_url}")
                continue
            
            # STRICT FILTER: Only allow URLs that start with the exact seed URL prefix
            # Extract exact prefix from seed URL (e.g., https://docs.appdynamics.com/appd/24.x/latest/en)
            seed_prefix = '/'.join(self.seed_url.split('/')[:7])  # Get up to /en
            if not absolute_url.startswith(seed_prefix):
                logger.debug(f"Skipping {absolute_url}: does not start with {seed_prefix}")
                self.stats['pages_skipped'] += 1
                continue
            
            # Canonicalize URL
            canonical_link = canonicalize_url(absolute_url)
            
            # Skip if already visited
            if canonical_link in self.visited_urls:
                continue
            
            # Check safety guards
            if not self._check_safety_guards(absolute_url):
                logger.debug(f"Safety guard blocked {absolute_url}")
                self.stats['pages_skipped'] += 1
                continue
            
            # Mark as visited
            self.visited_urls.add(canonical_link)
            
            # Write graph entry for link relationship
            if hasattr(self, 'crawler_instance') and self.crawler_instance:
                graph_entry = {
                    'source_url': response.url,
                    'target_url': absolute_url,
                    'link_type': 'internal',
                    'canonical_source': canonicalize_url(response.url),
                    'canonical_target': canonical_link,
                }
                self.crawler_instance.manifest_writer.write_graph_entry(graph_entry)
            
            # Create request for next depth level
            yield Request(
                url=absolute_url,
                callback=self.parse,
                errback=self.errback,
                meta={
                    'depth': depth + 1,
                    'canonical_url': canonical_link,
                }
            )
    
    def _extract_links(self, response: Response) -> list[str]:
        """
        Extract links from response.
        
        Args:
            response: Scrapy Response object
        
        Returns:
            List of link URLs
        """
        links = []
        
        # Extract all <a> tags with href attributes
        for link in response.css('a::attr(href)').getall():
            if link:
                links.append(link)
        
        return links
    
    def _check_safety_guards(self, url: str) -> bool:
        """
        Check URL against all safety guards.
        
        Args:
            url: URL to check
        
        Returns:
            True if URL passes all safety checks
        """
        # Check URL length
        if len(url) > self.config.safety.max_url_length:
            logger.debug(f"URL too long: {len(url)} > {self.config.safety.max_url_length}")
            return False
        
        # Check for random segments (UUID/entropy)
        has_random, segments = check_url_for_random_segments(
            url,
            self.config.safety.entropy_threshold
        )
        if has_random:
            logger.debug(f"Random identifier detected: {segments}")
            if self.config.safety.mode == "enforce":
                return False
        
        # Check parameter explosion
        is_explosion, reason = self.param_detector.check_url(url)
        if is_explosion:
            logger.debug(f"Parameter explosion: {reason}")
            if self.config.safety.mode == "enforce":
                return False
        
        # Check pagination limit
        if not self.pagination_detector.should_follow(url):
            logger.debug(f"Pagination limit reached for {url}")
            return False
        
        # Check blocked patterns
        for pattern in self.config.safety.blocked_patterns:
            import re
            if re.search(pattern, url):
                logger.debug(f"URL matches blocked pattern: {pattern}")
                if self.config.safety.mode == "enforce":
                    return False
        
        return True
    
    def errback(self, failure):
        """Handle request errors."""
        self.stats['errors'] += 1
        logger.error(f"Request failed: {failure.request.url} - {failure.value}")
