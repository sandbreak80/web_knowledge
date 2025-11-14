"""Crawl planner for dry-run mode."""

import logging
from typing import List, Optional
from urllib.parse import urlparse

from webarc.config.schema import WebArcConfig
from webarc.utils.url import extract_domain

logger = logging.getLogger(__name__)


class CrawlPlanner:
    """
    Plan crawl without actually fetching pages.
    """
    
    def __init__(
        self,
        seed_url: str,
        config: WebArcConfig,
        allowed_domain: Optional[str] = None,
        allowed_prefix: Optional[str] = None,
        max_depth: int = 3
    ):
        """
        Initialize crawl planner.
        
        Args:
            seed_url: Starting URL
            config: WebArc configuration
            allowed_domain: Domain restriction
            allowed_prefix: Path prefix restriction
            max_depth: Maximum crawl depth
        """
        self.seed_url = seed_url
        self.config = config
        self.allowed_domain = allowed_domain or config.allow_domain
        self.allowed_prefix = allowed_prefix or config.allow_prefix
        self.max_depth = max_depth or config.crawler.max_depth
    
    def plan(self) -> dict:
        """
        Generate crawl plan.
        
        Returns:
            Dictionary with plan details
        """
        plan = {
            'seed_url': self.seed_url,
            'allowed_domain': self.allowed_domain,
            'allowed_prefix': self.allowed_prefix,
            'max_depth': self.max_depth,
            'safety_mode': self.config.safety.mode,
            'respect_robots_txt': self.config.safety.respect_robots_txt,
            'estimated_pages': None,
            'sitemap_urls': [],
        }
        
        # Validate seed URL
        from webarc.safety.domain_fence import validate_domain_restriction
        
        allowed, reason = validate_domain_restriction(
            self.seed_url,
            self.allowed_domain,
            self.allowed_prefix
        )
        
        if not allowed:
            plan['error'] = f"Seed URL validation failed: {reason}"
            return plan
        
        # Try to discover sitemap
        sitemap_urls = self._discover_sitemap()
        plan['sitemap_urls'] = sitemap_urls
        plan['estimated_pages'] = len(sitemap_urls) if sitemap_urls else None
        
        return plan
    
    def _discover_sitemap(self) -> List[str]:
        """
        Discover sitemap URLs for the domain.
        
        Returns:
            List of URLs found in sitemaps
        """
        import requests
        from xml.etree import ElementTree as ET
        
        # Extract domain from seed URL
        domain = extract_domain(self.seed_url)
        parsed = urlparse(self.seed_url)
        scheme = parsed.scheme
        base_url = f"{scheme}://{domain}"
        
        urls = []
        
        # Common sitemap locations
        sitemap_candidates = [
            f"{base_url}/sitemap.xml",
            f"{base_url}/sitemap_index.xml",
            f"{base_url}/sitemap/sitemap.xml",
        ]
        
        # Also check robots.txt for sitemap directive
        try:
            robots_url = f"{base_url}/robots.txt"
            response = requests.get(robots_url, timeout=10, allow_redirects=True)
            if response.status_code == 200:
                for line in response.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith('sitemap:'):
                        sitemap_url = line.split(':', 1)[1].strip()
                        if sitemap_url:
                            sitemap_candidates.insert(0, sitemap_url)
        except Exception as e:
            logger.debug(f"Could not fetch robots.txt: {e}")
        
        # Try to fetch and parse sitemaps
        for sitemap_url in sitemap_candidates:
            try:
                response = requests.get(sitemap_url, timeout=10, allow_redirects=True)
                if response.status_code != 200:
                    continue
                
                # Parse XML
                try:
                    root = ET.fromstring(response.content)
                except ET.ParseError:
                    continue
                
                # Handle sitemap index (contains other sitemaps)
                if root.tag.endswith('sitemapindex'):
                    for sitemap_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}sitemap'):
                        loc_elem = sitemap_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                        if loc_elem is not None and loc_elem.text:
                            # Recursively fetch nested sitemap
                            nested_urls = self._parse_sitemap(loc_elem.text)
                            urls.extend(nested_urls)
                
                # Handle regular sitemap (contains URLs)
                elif root.tag.endswith('urlset'):
                    sitemap_urls = self._parse_sitemap(sitemap_url)
                    urls.extend(sitemap_urls)
                    break  # Found a valid sitemap, stop looking
                
            except Exception as e:
                logger.debug(f"Could not fetch/parse {sitemap_url}: {e}")
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def _parse_sitemap(self, sitemap_url: str) -> List[str]:
        """
        Parse a sitemap XML file and extract URLs.
        
        Args:
            sitemap_url: URL of the sitemap to parse
            
        Returns:
            List of URLs found in the sitemap
        """
        import requests
        from xml.etree import ElementTree as ET
        
        urls: List[str] = []
        
        try:
            response = requests.get(sitemap_url, timeout=10, allow_redirects=True)
            if response.status_code != 200:
                return urls
            
            root = ET.fromstring(response.content)
            
            # Extract URLs from urlset
            for url_elem in root.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
                loc_elem = url_elem.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
                if loc_elem is not None and loc_elem.text:
                    urls.append(loc_elem.text.strip())
        
        except Exception as e:
            logger.debug(f"Error parsing sitemap {sitemap_url}: {e}")
        
        return urls
