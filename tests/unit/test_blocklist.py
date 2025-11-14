"""Unit tests for blocklist functionality."""

import tempfile
from pathlib import Path
from webarc.safety.blocklist import load_blocklist, check_blocklist, reset_blocklist_cache


def test_load_blocklist():
    """Test loading blocklist from file."""
    reset_blocklist_cache()
    
    # Create temporary blocklist file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("# Comment line\n")
        f.write("0.0.0.0 bad-domain.com\n")
        f.write("0.0.0.0 another-bad.com\n")
        f.write("127.0.0.1 localhost\n")
        temp_path = f.name
    
    try:
        blocklist = load_blocklist(temp_path)
        assert len(blocklist) == 3
        assert "bad-domain.com" in blocklist
        assert "another-bad.com" in blocklist
        assert "localhost" in blocklist
    finally:
        Path(temp_path).unlink()


def test_check_blocklist():
    """Test checking domain against blocklist."""
    reset_blocklist_cache()
    
    # Create temporary blocklist file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("0.0.0.0 blocked.com\n")
        temp_path = f.name
    
    try:
        assert check_blocklist("blocked.com", temp_path) is True
        assert check_blocklist("allowed.com", temp_path) is False
        assert check_blocklist("www.blocked.com", temp_path) is True
    finally:
        Path(temp_path).unlink()


def test_blocklist_missing_file():
    """Test handling of missing blocklist file."""
    reset_blocklist_cache()
    blocklist = load_blocklist("/nonexistent/path/blocklist.txt")
    assert len(blocklist) == 0
