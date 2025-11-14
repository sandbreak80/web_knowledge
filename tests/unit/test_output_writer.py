"""Unit tests for output writer."""

import pytest
import tempfile
from pathlib import Path
from webarc.output.writer import OutputWriter
from webarc.config.loader import load_config


@pytest.fixture
def config():
    """Load test configuration."""
    return load_config()


def test_url_to_filepath(config):
    """Test URL to filepath conversion."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(Path(tmpdir), config)
        
        url = "https://docs.example.com/path/to/page"
        filepath = writer.url_to_filepath(url)
        
        assert "docs.example.com" in str(filepath)
        assert "path" in str(filepath)
        assert filepath.suffix == ".md"


def test_filename_sanitization(config):
    """Test filename sanitization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(Path(tmpdir), config)
        
        # Test invalid characters
        sanitized = writer._sanitize_filename("file<>name|test")
        assert "<" not in sanitized
        assert ">" not in sanitized
        assert "|" not in sanitized


def test_write_page(config):
    """Test writing a page."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(Path(tmpdir), config)
        
        content = {
            'markdown': '# Test Page\n\nContent here.',
            'metadata': {
                'title': 'Test Page',
                'source_url': 'https://example.com/page',
            },
            'content_hash': 'abc123',
        }
        
        filepath = writer.write_page("https://example.com/page", content)
        
        assert filepath.exists()
        assert filepath.suffix == ".md"
        
        # Check front-matter exists
        content_text = filepath.read_text()
        assert "---" in content_text
        assert "title:" in content_text


def test_write_page_deduplicates(config):
    """Duplicate content should reuse existing file via symlink or same content."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(Path(tmpdir), config)
        content = {
            "markdown": "# Page",
            "metadata": {"title": "Page"},
            "content_hash": "hash123",
        }
        first = writer.write_page("https://example.com/one", content)
        second = writer.write_page("https://example.com/two", content)
        assert first.exists()
        assert second.exists()
        assert writer.content_hashes["hash123"] == first
        assert writer.url_to_file["https://example.com/one"] == first
        # second might be symlink; resolve to compare
        assert second.resolve() == first.resolve()


def test_handle_collision_appends_suffix(config):
    """Existing file should trigger numeric suffix."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(Path(tmpdir), config)
        base = Path(tmpdir) / "file.md"
        base.write_text("existing")
        collided = writer._handle_collision(base)
        assert collided.name == "file-2.md"


def test_format_with_frontmatter_complex_metadata(config):
    """Complex metadata structures are dumped correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(Path(tmpdir), config)
        data = writer._format_with_frontmatter(
            {
                "metadata": {
                    "title": "Complex",
                    "tags": ["a", "b"],
                    "nested": {"key": "value"},
                    "note": "value:with:colon",
                },
                "markdown": "Body",
            }
        )
        assert "tags:" in data
        assert "nested:" in data
        assert 'note: "value:with:colon"' in data


def test_write_page_generates_hash_when_missing(config):
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = OutputWriter(Path(tmpdir), config)
        content = {"markdown": "# Body", "metadata": {}}
        path = writer.write_page("https://example.com/hashless", content)
        assert path.exists()
        assert any(writer.content_hashes.values())
