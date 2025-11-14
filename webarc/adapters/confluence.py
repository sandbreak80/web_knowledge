"""Confluence adapter for Confluence-based documentation."""

import re
from typing import Dict, List, Any
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from webarc.adapters.base import SiteAdapter
from webarc.config.schema import WebArcConfig
from webarc.utils.url import extract_domain


class ConfluenceAdapter(SiteAdapter):
    """
    Adapter for Confluence-based documentation (e.g., docs.appdynamics.com).
    """
    
    def __init__(self, config: WebArcConfig):
        """
        Initialize Confluence adapter.
        
        Args:
            config: WebArc configuration
        """
        self.config = config
    
    def matches(self, url: str, html: str) -> bool:
        """
        Detect Confluence pages.
        
        Args:
            url: Page URL
            html: HTML content
        
        Returns:
            True if this is a Confluence page
        """
        # Check domain configuration (handle both dict and object access)
        try:
            confluence_config = self.config.adapters.confluence
            if isinstance(confluence_config, dict):
                if confluence_config.get('enabled', True):
                    domain = extract_domain(url)
                    if domain in confluence_config.get('domains', []):
                        return True
            else:
                if confluence_config.enabled:
                    domain = extract_domain(url)
                    if domain in confluence_config.domains:
                        return True
        except (AttributeError, TypeError):
            pass
        
        # Check for Confluence meta tags
        if 'confluence' in html.lower() and 'viewport' in html.lower():
            return True
        
        # Check for Confluence-specific classes
        soup = BeautifulSoup(html, 'lxml')
        if soup.find(class_=lambda x: x and ('confluence-content' in str(x) or 'ia-fixed-sidebar' in str(x))):
            return True
        
        return False
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract content from Confluence page.
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Source URL
        
        Returns:
            Extracted content dictionary
        """
        # Extract title from H1
        h1 = soup.find('h1')
        title = h1.get_text(strip=True) if h1 else "Untitled"
        
        # Find main content container
        try:
            content_selector = self.config.adapters.confluence.content_selector
            remove_selectors = self.config.adapters.confluence.remove_selectors
        except AttributeError:
            # Fallback if config structure is different
            content_selector = ".confluence-content"
            remove_selectors = [".ia-fixed-sidebar", ".page-metadata", ".footer"]
        
        main_content = soup.select_one(content_selector)
        
        if not main_content:
            # Fallback: find nearest meaningful container to H1
            main_content = h1.find_parent(['div', 'article', 'main']) if h1 else soup.body
        
        if main_content is None:
            main_content = soup.body
        
        # Create a copy to avoid modifying original
        main_content = BeautifulSoup(str(main_content), 'lxml')
        
        # Remove unwanted elements
        for selector in remove_selectors:
            for element in main_content.select(selector):
                element.decompose()

        # Remove additional navigation / export widgets and inline styles
        extra_selectors = [
            '.appdtocbox',
            '.scroll-pdf-modal',
            '.page-metadata',
            '.pdf',
            '.scroll-to-top',
            'header',
            'nav',
            '.breadcrumbs',
            '.js-breadcrumbs-truncate',
        ]
        for selector in extra_selectors:
            for element in main_content.select(selector):
                element.decompose()

        for style_tag in main_content.find_all('style'):
            style_tag.decompose()
        
        # Extract version from URL if present
        # Example: /appd/24.x/ → version: "24.x"
        version = None
        version_match = re.search(r'/appd/([^/]+)/', url)
        if version_match:
            version = version_match.group(1)
        
        # Extract language
        html_tag = soup.find('html')
        lang = html_tag.get('lang', 'en') if html_tag else 'en'
        
        return {
            "title": title,
            "body_html": str(main_content),
            "version": version,
            "lang": lang,
            "framework": "confluence-viewport",
            "remove_selectors": remove_selectors,
            "metadata": {
                "extracted_with": "ConfluenceAdapter"
            }
        }
    
    def transform_links(self, source_url: str, links: List[str]) -> List[str]:
        """
        Convert Confluence links to relative wikilinks.
        
        Args:
            source_url: Source page URL
            links: List of link URLs
        
        Returns:
            List of transformed links
        """
        transformed = []
        
        for link in links:
            # Keep version prefix
            # /appd/24.x/en/page → [[page]]
            # But preserve version branch
            if '/appd/' in link:
                # Ensure we stay within version
                if not self._is_same_version(source_url, link):
                    # External link to different version
                    transformed.append(f"[External]({link})")
                else:
                    # Convert to wikilink
                    slug = self._url_to_slug(link)
                    transformed.append(f"[[{slug}]]")
            else:
                transformed.append(link)
        
        return transformed
    
    def _is_same_version(self, url1: str, url2: str) -> bool:
        """Check if URLs are in same version branch."""
        version1 = re.search(r'/appd/([^/]+)/', url1)
        version2 = re.search(r'/appd/([^/]+)/', url2)
        
        if version1 and version2:
            return version1.group(1) == version2.group(1)
        
        return False
    
    def _url_to_slug(self, url: str) -> str:
        """Convert URL to Obsidian slug."""
        # /appd/24.x/en/splunk-appdynamics-essentials → splunk-appdynamics-essentials
        path = urlparse(url).path
        slug = path.split('/')[-1]
        return slug or "index"
