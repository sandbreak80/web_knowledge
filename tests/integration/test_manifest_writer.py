"""Integration tests for ManifestWriter."""

import tempfile
from pathlib import Path
import orjson

from webarc.output.manifest import ManifestWriter


def test_manifest_writer_initialization():
    """Test ManifestWriter initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = ManifestWriter(Path(tmpdir))
        assert writer.output_dir == Path(tmpdir)
        assert writer.manifest_file == Path(tmpdir) / 'manifest.jsonl'
        assert writer.graph_file == Path(tmpdir) / 'graph.jsonl'
        assert writer.errors_file == Path(tmpdir) / 'errors.jsonl'


def test_write_manifest_entry():
    """Test writing manifest entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = ManifestWriter(Path(tmpdir))
        
        entry = {
            'url': 'https://example.com/page',
            'file_path': 'page.md',
            'title': 'Test Page',
            'word_count': 100,
        }
        
        writer.write_manifest_entry(entry)
        
        # Verify file exists and content
        assert writer.manifest_file.exists()
        with open(writer.manifest_file, 'rb') as f:
            content = f.read()
            loaded = orjson.loads(content)
            assert loaded['url'] == 'https://example.com/page'
            assert loaded['title'] == 'Test Page'


def test_write_graph_entry():
    """Test writing graph entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = ManifestWriter(Path(tmpdir))
        
        entry = {
            'source_url': 'https://example.com/page1',
            'target_url': 'https://example.com/page2',
            'link_type': 'internal',
        }
        
        writer.write_graph_entry(entry)
        
        # Verify file exists and content
        assert writer.graph_file.exists()
        with open(writer.graph_file, 'rb') as f:
            content = f.read()
            loaded = orjson.loads(content)
            assert loaded['source_url'] == 'https://example.com/page1'
            assert loaded['target_url'] == 'https://example.com/page2'


def test_write_error_entry():
    """Test writing error entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = ManifestWriter(Path(tmpdir))
        
        entry = {
            'url': 'https://example.com/page',
            'error_type': 'PROCESSING_ERROR',
            'error_message': 'Test error',
        }
        
        writer.write_error_entry(entry)
        
        # Verify file exists and content
        assert writer.errors_file.exists()
        with open(writer.errors_file, 'rb') as f:
            content = f.read()
            loaded = orjson.loads(content)
            assert loaded['url'] == 'https://example.com/page'
            assert loaded['error_type'] == 'PROCESSING_ERROR'


def test_multiple_entries():
    """Test writing multiple entries."""
    with tempfile.TemporaryDirectory() as tmpdir:
        writer = ManifestWriter(Path(tmpdir))
        
        # Write multiple manifest entries
        for i in range(3):
            writer.write_manifest_entry({
                'url': f'https://example.com/page{i}',
                'file_path': f'page{i}.md',
            })
        
        # Verify all entries are present
        entries = []
        with open(writer.manifest_file, 'rb') as f:
            for line in f:
                if line.strip():
                    entries.append(orjson.loads(line))
        
        assert len(entries) == 3
        assert entries[0]['url'] == 'https://example.com/page0'
        assert entries[2]['url'] == 'https://example.com/page2'
