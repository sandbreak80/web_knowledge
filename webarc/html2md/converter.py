"""HTML to Obsidian Markdown conversion."""

import re
from typing import Optional
from bs4 import BeautifulSoup
from markdownify import markdownify as md

from webarc.config.schema import WebArcConfig


class ObsidianMarkdownConverter:
    """
    Convert HTML to Obsidian-flavored Markdown.
    """
    
    def __init__(self, config: WebArcConfig):
        """
        Initialize Markdown converter.
        
        Args:
            config: WebArc configuration
        """
        self.config = config
    
    def convert(self, html: str, source_url: str) -> str:
        """
        Convert HTML to clean Markdown.
        
        Args:
            html: HTML content
            source_url: Source URL
        
        Returns:
            Markdown content
        """
        soup = BeautifulSoup(html, 'lxml')
        
        # 1. Transform admonitions BEFORE markdownify
        self._transform_admonitions(soup)
        
        # 2. Transform links
        self._transform_links(soup, source_url)
        
        # 3. Transform images
        self._transform_images(soup, source_url)
        
        # 4. Convert to Markdown
        markdown = md(
            str(soup),
            heading_style='ATX',           # Use # for headings
            bullets='-',                   # Use - for unordered lists
            code_language='',              # Preserve language hints
            strip=['script', 'style'],     # Remove these tags
            escape_asterisks=False,        # Don't escape * in text
            escape_underscores=False,      # Don't escape _
        )
        
        # 5. Post-process
        markdown = self._post_process(markdown)
        
        return markdown
    
    def _transform_admonitions(self, soup: BeautifulSoup):
        """Convert framework-specific admonitions to Obsidian callouts."""
        # Confluence admonitions
        confluence_map = {
            'ac:info': 'INFO',
            'ac:note': 'NOTE',
            'ac:warning': 'WARNING',
            'ac:tip': 'TIP',
        }
        
        for tag_name, callout_type in confluence_map.items():
            for element in soup.find_all(tag_name):
                if element is None or not hasattr(element, "get"):
                    continue
                blockquote = soup.new_tag('blockquote')
                blockquote.string = f"[!{callout_type}]\n{element.get_text()}"
                element.replace_with(blockquote)
        
        # MkDocs admonitions (class-based)
        admonition_map = {
            'note': 'NOTE',
            'tip': 'TIP',
            'warning': 'WARNING',
            'danger': 'DANGER',
            'info': 'INFO',
        }
        
        for element in soup.find_all(class_=lambda x: x and 'admonition' in str(x).lower()):
            if element is None or not hasattr(element, "get"):
                continue
            try:
                classes = element.get('class', []) or []
            except AttributeError:
                continue
            for key, callout_type in admonition_map.items():
                if key in classes:
                    blockquote = soup.new_tag('blockquote')
                    
                    # Extract title if present
                    title_el = element.find(class_=lambda x: x and 'admonition-title' in str(x).lower())
                    title = title_el.get_text() if title_el else ''
                    
                    # Extract content
                    if title_el:
                        title_el.decompose()
                    content = element.get_text()
                    
                    # Format as Obsidian callout
                    callout_text = f"[!{callout_type}]"
                    if title:
                        callout_text += f" {title}"
                    callout_text += f"\n{content}"
                    
                    blockquote.string = callout_text
                    element.replace_with(blockquote)
                    break
    
    def _transform_links(self, soup: BeautifulSoup, source_url: str):
        """Convert links to Obsidian format."""
        from urllib.parse import urljoin
        from webarc.utils.url import is_same_domain
        
        for link in soup.find_all('a'):
            href = link.get('href', '')
            
            if not href:
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(source_url, href)
            
            # Check if internal or external
            if is_same_domain(source_url, absolute_url):
                # Convert to wikilink or relative markdown link
                if self.config.output.obsidian_link_style == 'wikilink':
                    slug = self._url_to_slug(absolute_url)
                    anchor = self._extract_anchor(absolute_url)
                    
                    link_text = link.get_text()
                    
                    # Format: [[slug#anchor|display text]]
                    wikilink = f"[[{slug}"
                    if anchor:
                        wikilink += f"#{anchor}"
                    if link_text and link_text != slug:
                        wikilink += f"|{link_text}"
                    wikilink += "]]"
                    
                    # Replace link with text containing wikilink
                    link.string = wikilink
                    link.name = 'span'  # Convert <a> to <span>
                else:
                    # Use relative markdown links
                    rel_path = self._relative_path(source_url, absolute_url)
                    link['href'] = rel_path
            else:
                # Keep external links as absolute
                link['href'] = absolute_url
    
    def _transform_images(self, soup: BeautifulSoup, source_url: str):
        """Handle images based on config."""
        from urllib.parse import urljoin
        
        for img in soup.find_all('img'):
            src = img.get('src', '')
            
            if not src:
                continue
            
            # Resolve relative URLs
            absolute_url = urljoin(source_url, src)
            
            if self.config.output.image_mode == 'ignore':
                # Keep as reference to original URL
                img['src'] = absolute_url
            # Note: download and embed modes not implemented yet
    
    def _post_process(self, markdown: str) -> str:
        """Clean up converted Markdown."""
        # Remove excessive blank lines (3+ → 2)
        markdown = re.sub(r'\n{3,}', '\n\n', markdown)
        
        # Ensure proper spacing around headings
        markdown = re.sub(r'(^|\n)(#{1,6})', r'\1\n\2', markdown)
        
        return markdown.strip()
    
    def _url_to_slug(self, url: str) -> str:
        """Convert URL to Obsidian-safe slug."""
        from urllib.parse import urlparse
        
        path = urlparse(url).path
        
        # Get last path segment
        slug = path.rstrip('/').split('/')[-1]
        
        # Remove file extension
        slug = re.sub(r'\.(html?|php|aspx?)$', '', slug)
        
        # Use 'index' for empty slugs
        if not slug:
            slug = 'index'
        
        return slug
    
    def _extract_anchor(self, url: str) -> Optional[str]:
        """Extract #anchor from URL."""
        from urllib.parse import urlparse
        
        fragment = urlparse(url).fragment
        return fragment if fragment else None
    
    def _relative_path(self, source_url: str, target_url: str) -> str:
        """Calculate relative path from source to target."""
        from urllib.parse import urlparse
        
        target_path = urlparse(target_url).path
        
        # Simplified: return target path
        return target_path
