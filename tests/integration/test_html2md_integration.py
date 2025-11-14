"""Integration coverage for the HTML→Markdown converter."""

from webarc.config.loader import load_config
from webarc.html2md.converter import ObsidianMarkdownConverter


def test_converter_handles_admonitions_and_links():
    config = load_config()
    config.output.obsidian_link_style = "wikilink"
    converter = ObsidianMarkdownConverter(config)
    html = """
    <html>
      <body>
        <ac:note>Remember this</ac:note>
        <div class="admonition warning">
          <p class="admonition-title">Heads up</p>
          <p>Warning text</p>
        </div>
        <a href="/docs/page#section">Internal</a>
        <img src="images/pic.png" />
      </body>
    </html>
    """
    config.output.image_mode = "ignore"
    markdown = converter.convert(html, "https://example.com/docs/start")
    assert "[!NOTE]" in markdown
    assert "[!WARNING] Heads up" in markdown
    assert "[[page#section|Internal]]" in markdown
    assert "https://example.com/docs/images/pic.png" in markdown

