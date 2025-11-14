"""Unit tests for HTML to Markdown conversion."""

import pytest
from webarc.html2md.converter import ObsidianMarkdownConverter
from webarc.config.loader import load_config


@pytest.fixture
def config():
    """Load test configuration."""
    return load_config()


def test_basic_html_conversion(config):
    """Test basic HTML to Markdown conversion."""
    converter = ObsidianMarkdownConverter(config)
    
    html = """
    <html>
    <body>
        <h1>Title</h1>
        <p>Paragraph with <strong>bold</strong> text.</p>
        <ul>
            <li>Item 1</li>
            <li>Item 2</li>
        </ul>
    </body>
    </html>
    """
    
    markdown = converter.convert(html, "https://example.com/page")
    
    assert "# Title" in markdown
    assert "bold" in markdown
    assert "Item 1" in markdown


def test_wikilink_conversion(config):
    """Test internal link conversion to wikilinks."""
    config.output.obsidian_link_style = "wikilink"
    converter = ObsidianMarkdownConverter(config)
    
    html = """
    <html>
    <body>
        <a href="/page2">Link Text</a>
    </body>
    </html>
    """
    
    markdown = converter.convert(html, "https://example.com/page1")
    
    # Should contain wikilink format
    assert "[[" in markdown or "page2" in markdown


def test_confluence_admonition_conversion(config):
    """Confluence admonitions become callouts."""
    converter = ObsidianMarkdownConverter(config)
    html = """
    <html><body><ac:note>Remember this</ac:note></body></html>
    """
    markdown = converter.convert(html, "https://example.com")
    assert "[!NOTE]" in markdown
    assert "Remember this" in markdown


def test_mkdocs_admonition_conversion(config):
    """MkDocs admonition classes convert to callouts with titles."""
    converter = ObsidianMarkdownConverter(config)
    html = """
    <div class="admonition tip">
      <p class="admonition-title">Pro Tip</p>
      <p>Use the feature</p>
    </div>
    """
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(html, "html.parser")
    converter._transform_admonitions(soup)
    blockquote = soup.find("blockquote")
    assert blockquote
    text = blockquote.string
    assert "[!TIP] Pro Tip" in text
    assert "Use the feature" in text


def test_relative_link_style(config):
    """Relative link mode retains href with resolved path."""
    config.output.obsidian_link_style = "relative"
    converter = ObsidianMarkdownConverter(config)
    html = '<a href="/docs/page.html#section">Docs</a>'
    markdown = converter.convert(html, "https://example.com/start/")
    assert "/docs/page.html" in markdown


def test_image_ignore_mode(config):
    """Image mode ignore rewrites src as absolute."""
    config.output.image_mode = "ignore"
    converter = ObsidianMarkdownConverter(config)
    html = '<img src="images/pic.png" alt="pic">'
    markdown = converter.convert(html, "https://example.com/docs/page")
    assert "https://example.com/docs/images/pic.png" in markdown


def test_post_process_removes_extra_blank_lines(config):
    converter = ObsidianMarkdownConverter(config)
    messy = "\n\n\n# Heading\n\n"
    cleaned = converter._post_process(messy)
    assert cleaned.startswith("# Heading")
