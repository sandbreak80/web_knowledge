"""Integration tests for StateManager."""

import tempfile
from pathlib import Path
import orjson

from webarc.crawler.state import StateManager


def test_state_manager_initialization():
    """Test StateManager initialization."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StateManager(Path(tmpdir))
        assert manager.output_dir == Path(tmpdir)
        assert manager.resume_file == Path(tmpdir) / 'resume.jsonl'
        assert manager.checkpoint_interval == 100
        assert manager.pages_since_checkpoint == 0


def test_save_state():
    """Test saving crawler state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StateManager(Path(tmpdir))
        
        crawler_state = {
            'seed_url': 'https://example.com',
            'pages_crawled': 10,
            'pages_extracted': 8,
            'pages_skipped': 2,
            'pages_failed': 0,
            'queue': ['https://example.com/page1'],
            'visited': ['https://example.com'],
            'status': 'running',
        }
        
        manager.save_state(crawler_state)
        
        # Verify file exists
        assert manager.resume_file.exists()
        
        # Verify content
        with open(manager.resume_file, 'rb') as f:
            content = f.read()
            state = orjson.loads(content)
            assert state['seed_url'] == 'https://example.com'
            assert state['pages_crawled'] == 10
            assert state['pages_queued'] == 1
            assert state['status'] == 'running'


def test_load_state():
    """Test loading crawler state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StateManager(Path(tmpdir))
        
        # Save state first
        crawler_state = {
            'seed_url': 'https://example.com',
            'pages_crawled': 5,
            'queue': [],
            'visited': ['https://example.com'],
            'status': 'running',
        }
        manager.save_state(crawler_state)
        
        # Load state
        loaded = manager.load_state()
        assert loaded is not None
        assert loaded['seed_url'] == 'https://example.com'
        assert loaded['pages_crawled'] == 5


def test_load_state_not_found():
    """Test loading state when file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StateManager(Path(tmpdir))
        loaded = manager.load_state()
        assert loaded is None


def test_maybe_checkpoint():
    """Test checkpoint interval logic."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = StateManager(Path(tmpdir), checkpoint_interval=3)
        
        crawler_state = {
            'seed_url': 'https://example.com',
            'pages_crawled': 1,
            'queue': [],
            'visited': [],
            'status': 'running',
        }
        
        # Should not checkpoint yet
        manager.maybe_checkpoint(crawler_state)
        assert not manager.resume_file.exists()
        assert manager.pages_since_checkpoint == 1
        
        # Should not checkpoint yet
        manager.maybe_checkpoint(crawler_state)
        assert not manager.resume_file.exists()
        assert manager.pages_since_checkpoint == 2
        
        # Should checkpoint now
        manager.maybe_checkpoint(crawler_state)
        assert manager.resume_file.exists()
        assert manager.pages_since_checkpoint == 0
