"""Generic adapter using readability-lxml as fallback."""

from typing import Dict, List, Any
from bs4 import BeautifulSoup

from webarc.adapters.base import SiteAdapter
from webarc.config.schema import WebArcConfig
from webarc.extractors.boilerplate import extract_main_content


class GenericAdapter(SiteAdapter):
    """
    Generic adapter using readability-lxml as fallback.
    """
    
    def __init__(self, config: WebArcConfig):
        """
        Initialize generic adapter.
        
        Args:
            config: WebArc configuration
        """
        self.config = config
    
    def matches(self, url: str, html: str) -> bool:
        """
        Generic adapter always matches (used as fallback).
        
        Args:
            url: Page URL
            html: HTML content
        
        Returns:
            True (always matches as fallback)
        """
        return True
    
    def extract_content(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """
        Extract content using readability-lxml.
        
        Args:
            soup: BeautifulSoup parsed HTML
            url: Source URL
        
        Returns:
            Extracted content dictionary
        """
        html_str = str(soup)
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text(strip=True) if title_tag else "Untitled"
        
        # Use readability to extract main content
        body_html = extract_main_content(html_str, url)
        extracted_word_count = 0
        
        if body_html:
            summary_soup = BeautifulSoup(body_html, 'lxml')
            summary_text = summary_soup.get_text(separator=' ', strip=True)
            extracted_word_count = len(summary_text.split())
        
        if not body_html:
            # Fallback: use body content
            body = soup.find('body')
            body_html = str(body) if body else html_str
        elif extracted_word_count < self.config.extraction.min_word_count:
            # If readability result is too small, fallback to structural main content
            fallback_candidates: List[Any] = []
            
            main_tag = soup.find('main')
            if main_tag:
                fallback_candidates.append(main_tag)
            
            role_main = soup.find(attrs={"role": "main"})
            if role_main and role_main not in fallback_candidates:
                fallback_candidates.append(role_main)
            
            sqs_layout = soup.select_one('.sqs-layout')
            if sqs_layout and sqs_layout not in fallback_candidates:
                fallback_candidates.append(sqs_layout)
            
            body = soup.find('body')
            if body:
                fallback_candidates.append(body)
            
            for candidate in fallback_candidates:
                text = candidate.get_text(separator=' ', strip=True)
                if len(text.split()) >= self.config.extraction.min_word_count:
                    body_html = str(candidate)
                    break
        
        # Extract language
        html_tag = soup.find('html')
        lang = html_tag.get('lang', 'en') if html_tag else 'en'
        
        return {
            "title": title,
            "body_html": body_html,
            "version": None,
            "lang": lang,
            "framework": "generic",
            "remove_selectors": [],
            "metadata": {
                "extracted_with": "GenericAdapter"
            }
        }
    
    def transform_links(self, source_url: str, links: List[str]) -> List[str]:
        """
        Transform links (generic - no special transformation).
        
        Args:
            source_url: Source page URL
            links: List of link URLs
        
        Returns:
            List of links (unchanged for generic adapter)
        """
        return links
