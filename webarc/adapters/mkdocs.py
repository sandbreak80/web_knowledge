"""MkDocs adapter for MkDocs-based documentation."""

import re
from typing import Dict, List, Any
from bs4 import BeautifulSoup

from webarc.adapters.base import SiteAdapter
from webarc.config.schema import WebArcConfig
from webarc.extractors.boilerplate import extract_main_content


class MkDocsAdapter(SiteAdapter):
    """
    Adapter for MkDocs-based documentation.
    """
    
    def __init__(self, config: WebArcConfig):
        """
        Initialize MkDocs adapter.
        
        Args:
            config: WebArc configuration
        """
        self.config = config
    
    def matches(self, url: str, html: str) -> bool:
        """
        Detect MkDocs pages.
        
        Args:
            url: Page URL
            html: HTML content
        
        Returns:
            True if this is a MkDocs page
        """
        # Check if adapter is enabled
        try:
            mkdocs_config = self.config.adapters.mkdocs
            if isinstance(mkdocs_config, dict):
                if not mkdocs_config.get('enabled', True):
                    return False
            else:
                if not mkdocs_config.enabled:
                    return False
        except Exception:
            pass
        
        # Detect MkDocs by HTML structure
        soup = BeautifulSoup(html, 'html.parser')
        
        # Common MkDocs indicators
        mkdocs_indicators = [
            soup.find('div', class_=re.compile(r'md-', re.I)),
            soup.find('nav', class_=re.compile(r'md-nav', re.I)),
            soup.find('div', class_=re.compile(r'md-content', re.I)),
            soup.find('div', class_=re.compile(r'md-main', re.I)),
            soup.find('div', class_=re.compile(r'md-sidebar', re.I)),
            soup.find('div', class_=re.compile(r'md-header', re.I)),
            soup.find('meta', {'name': 'generator', 'content': re.compile(r'mkdocs', re.I)}),
        ]
        
        return any(mkdocs_indicators)
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract content from MkDocs page.
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Source URL
        
        Returns:
            Extracted content dictionary
        """
        # Get content selector from config
        try:
            mkdocs_config = self.config.adapters.mkdocs
            if isinstance(mkdocs_config, dict):
                content_selector = mkdocs_config.get('content_selector', '.md-content')
                remove_selectors = mkdocs_config.get('remove_selectors', ['.md-sidebar', '.md-header'])
            else:
                content_selector = mkdocs_config.content_selector
                remove_selectors = mkdocs_config.remove_selectors
        except Exception:
            content_selector = '.md-content'
            remove_selectors = ['.md-sidebar', '.md-header']
        
        # Extract title
        title_tag = soup.find('title')
        if not title_tag:
            # Try h1 in content area
            content_area = soup.select_one(content_selector)
            if content_area:
                h1 = content_area.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
                else:
                    title = "Untitled"
            else:
                title = "Untitled"
        else:
            title = title_tag.get_text(strip=True)
        
        # Find main content area
        content_area = soup.select_one(content_selector)
        if not content_area:
            # Fallback: try common MkDocs content areas
            for selector in ['.md-content', 'article', 'main', '.content']:
                content_area = soup.select_one(selector)
                if content_area:
                    break
        
        if content_area:
            # Remove unwanted elements
            for selector in remove_selectors:
                for elem in content_area.select(selector):
                    elem.decompose()
            
            body_html = str(content_area)
        else:
            # Fallback to readability
            html_str = str(soup)
            body_html = extract_main_content(html_str, url)
            if not body_html:
                body = soup.find('body')
                body_html = str(body) if body else html_str
        
        # Extract language
        html_tag = soup.find('html')
        lang = html_tag.get('lang', 'en') if html_tag else 'en'
        
        return {
            "title": title,
            "body_html": body_html,
            "version": None,
            "lang": lang,
            "framework": "mkdocs",
            "remove_selectors": remove_selectors,
            "metadata": {
                "extracted_with": "MkDocsAdapter"
            }
        }
    
    def transform_links(self, source_url: str, links: List[str]) -> List[str]:
        """
        Transform links to Obsidian format.
        
        Args:
            source_url: Source page URL
            links: List of link URLs
        
        Returns:
            List of transformed links
        """
        # MkDocs links are typically already clean, but we can normalize
        return links
